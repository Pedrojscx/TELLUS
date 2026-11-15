"""Regras puras de vegetação (Princípio VI): sem rede, sem relógio, sem estado oculto.

Os fatos de produto (escala, faixa válida, bits de QA, grade senoidal) vêm de
referencias/vegetacao/produtos.json. A regra de qualidade e o índice são parâmetros recebidos
de fora (parametros.json, status hipotese/decisao_pendente até a decisão D-007, issue #69).
Nada aqui interpola, preenche ou estima valor ausente: dado sem qualidade vira lacuna.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Mapping, Sequence

from tellus.car.regras import pontos_amostra

# ---------------------------------------------------------------- grade senoidal MODIS


def xy_senoidal(lat: float, lon: float, grade: Mapping) -> tuple[float, float]:
    """Projeção senoidal do MODIS: x = R·λ·cos φ, y = R·φ (radianos)."""
    r = grade["raio_terra_m"]
    phi, lam = math.radians(lat), math.radians(lon)
    return r * lam * math.cos(phi), r * phi


def pixel_de_xy(x: float, y: float, grade: Mapping) -> str:
    """Identificador estável do pixel de 250 m: tile hHHvVV, linha e coluna dentro do tile."""
    lado = grade["lado_tile_m"]
    n = grade["pixels_por_tile_250m"]
    passo = lado / n
    dx, dy = x - grade["x_min_m"], grade["y_max_m"] - y
    h, v = math.floor(dx / lado), math.floor(dy / lado)
    col = math.floor(round((dx - h * lado) / passo, 9))
    lin = math.floor(round((dy - v * lado) / passo, 9))
    return f"h{h:02d}v{v:02d}.l{lin:04d}.c{col:04d}"


def pixel_senoidal(lat: float, lon: float, grade: Mapping) -> str:
    return pixel_de_xy(*xy_senoidal(lat, lon, grade), grade)


def pesos_pixels(geometria: dict, grade: Mapping, max_pontos: int = 2500) -> dict[str, float]:
    """Fração da área em cada pixel MODIS. Ponto: peso 1. Polígono: amostragem regular (soma 1)."""
    if geometria["type"] == "Point":
        lon, lat = geometria["coordinates"][:2]
        return {pixel_senoidal(lat, lon, grade): 1.0}
    contagem: dict[str, int] = {}
    for lat, lon in pontos_amostra(geometria, max_pontos):
        p = pixel_senoidal(lat, lon, grade)
        contagem[p] = contagem.get(p, 0) + 1
    total = sum(contagem.values())
    return {p: n / total for p, n in sorted(contagem.items())}


# ---------------------------------------------------------------- calendário das composições


def fim_composicao(inicio: dt.date, passo_dias: int) -> dt.date:
    """Última data da janela de composição; a última do ano termina em 31/12."""
    return min(inicio + dt.timedelta(days=passo_dias - 1), dt.date(inicio.year, 12, 31))


def calendario(inicio: dt.date, fim: dt.date, dia_inicial: int, passo_dias: int) -> list[dt.date]:
    """Datas de início das composições do produto (dia juliano inicial e passo fixos) em [inicio, fim]."""
    datas = []
    for ano in range(inicio.year, fim.year + 1):
        d = dt.date(ano, 1, 1) + dt.timedelta(days=dia_inicial - 1)
        while d.year == ano:
            if inicio <= d <= fim:
                datas.append(d)
            d += dt.timedelta(days=passo_dias)
    return datas


# ---------------------------------------------------------------- qualidade por pixel

MOTIVO_RELIABILITY = {-1: "sem_dado", 1: "dado_marginal", 2: "neve_gelo", 3: "nuvem"}
BITS_FMASK = {0: "cirro", 1: "nuvem", 2: "adjacente_nuvem_sombra", 3: "sombra_nuvem", 4: "neve_gelo", 5: "agua"}


MOTIVO_BIT_VI_QUALITY = {8: "nuvem_adjacente", 10: "nuvem_mista", 14: "possivel_neve_gelo", 15: "possivel_sombra"}
VI_QUALITY_PREENCHIMENTO = 65535


def valor_modis(
    bruto: int | None, reliability: int | None, meta_indice: Mapping, regra: Mapping, vi_quality: int | None = None
) -> tuple[float | None, str | None]:
    """(valor, None) se o pixel passa na regra; (None, motivo) caso contrário. Nunca estima.

    Rank em `pixel_reliability_aceitos` vira valor. Rank em `pixel_reliability_condicionais`
    (marginal) só vira valor se a VI Quality disser 'VI produzido' (bits 0–1) e nenhum bit de
    `condicional_bits_vi_quality_rejeitados` estiver ligado; sem VI Quality, vira lacuna.
    """
    if bruto is None or reliability is None:
        return None, "sem_dado"
    if bruto == meta_indice["preenchimento"]:
        return None, "sem_dado"
    lo, hi = meta_indice["faixa_valida"]
    if not lo <= bruto <= hi:
        return None, "fora_da_faixa_valida"
    if reliability in regra["pixel_reliability_aceitos"]:
        return round(bruto * meta_indice["fator_escala"], 4), None
    if reliability in regra.get("pixel_reliability_condicionais", []):
        if vi_quality is None or vi_quality == VI_QUALITY_PREENCHIMENTO:
            return None, "dado_marginal"
        if vi_quality & 0b11 not in regra["condicional_modland_aceitos"]:
            return None, "dado_marginal"
        for bit in regra["condicional_bits_vi_quality_rejeitados"]:
            if vi_quality >> bit & 1:
                return None, MOTIVO_BIT_VI_QUALITY.get(bit, "dado_marginal")
        return round(bruto * meta_indice["fator_escala"], 4), None
    return None, MOTIVO_RELIABILITY.get(reliability, "qualidade_rejeitada")


def bandeiras_fmask(fmask: int) -> list[str]:
    return [nome for bit, nome in BITS_FMASK.items() if fmask >> bit & 1]


def indice_reflectancia(indice: str, vermelho: float, nir: float, azul: float | None = None) -> float | None:
    """NDVI ou EVI a partir de reflectância (0–1). None se o denominador zera."""
    if indice == "ndvi":
        den = nir + vermelho
        return None if den == 0 else (nir - vermelho) / den
    if indice == "evi":
        if azul is None:
            return None
        den = nir + 6 * vermelho - 7.5 * azul + 1
        return None if den == 0 else 2.5 * (nir - vermelho) / den
    raise ValueError(f"índice não suportado: {indice}")


def valor_hls(
    bandas: Mapping[str, int | None], fmask: int | None, indice: str, meta_bandas: Mapping, regra: Mapping
) -> tuple[float | None, str | None]:
    """Valor do índice HLS para um pixel, ou lacuna com motivo (Fmask ou preenchimento)."""
    if fmask is None:
        return None, "sem_dado"
    for bit in regra["fmask_bits_rejeitados"]:
        if fmask >> bit & 1:
            return None, BITS_FMASK.get(bit, "qualidade_rejeitada")
    precisa = ["vermelho", "nir"] + (["azul"] if indice == "evi" else [])
    for b in precisa:
        if bandas.get(b) is None or bandas[b] == meta_bandas["preenchimento"]:
            return None, "sem_dado"
    esc = meta_bandas["fator_escala"]
    v = indice_reflectancia(
        indice, bandas["vermelho"] * esc, bandas["nir"] * esc, bandas["azul"] * esc if bandas.get("azul") is not None else None
    )
    if v is None:
        return None, "sem_dado"
    return round(v, 4), None


# ---------------------------------------------------------------- agregação na área


def agregar_area(
    por_pixel: Mapping[str, tuple[float | None, str | None]], pesos: Mapping[str, float], cobertura_minima: float
) -> dict:
    """Média ponderada dos pixels válidos, se a fração válida (por peso) atinge `cobertura_minima`.

    Pixel sem registro no cache conta como `ausente_no_cache`. Abaixo da cobertura mínima, o valor
    é None e o motivo é o motivo de maior peso entre os pixels inválidos. Nada é preenchido.
    """
    soma_w = soma_v = 0.0
    motivos: dict[str, float] = {}
    for p, w in sorted(pesos.items()):
        if w <= 0:
            continue
        v, m = por_pixel.get(p, (None, "ausente_no_cache"))
        if v is None:
            motivos[m or "sem_dado"] = motivos.get(m or "sem_dado", 0.0) + w
        else:
            soma_w += w
            soma_v += w * v
    total = sum(w for w in pesos.values() if w > 0)
    cobertura = round(soma_w / total, 4) if total else 0.0
    contagem = {m: round(w / total, 4) for m, w in sorted(motivos.items())} if total else {}
    if total == 0 or soma_w == 0 or cobertura + 1e-9 < cobertura_minima:
        motivo = max(sorted(motivos), key=lambda k: motivos[k]) if motivos else "sem_dado"
        return {"valor": None, "motivo": motivo, "cobertura_valida": cobertura, "fracao_por_motivo": contagem}
    return {"valor": round(soma_v / soma_w, 4), "motivo": None, "cobertura_valida": cobertura, "fracao_por_motivo": contagem}


def sazonalidade_mensal(observacoes: Sequence[tuple[dt.date, float | None]]) -> list[dict]:
    """Média, mínimo e máximo por mês do ano, só com composições válidas; lacunas só são contadas."""
    meses: dict[int, list[float | None]] = {}
    for d, v in observacoes:
        meses.setdefault(d.month, []).append(v)
    saida = []
    for mes in sorted(meses):
        validos = [v for v in meses[mes] if v is not None]
        saida.append({
            "mes": mes,
            "media": round(sum(validos) / len(validos), 4) if validos else None,
            "minimo": min(validos) if validos else None,
            "maximo": max(validos) if validos else None,
            "n_validas": len(validos),
            "n_composicoes": len(meses[mes]),
        })
    return saida
