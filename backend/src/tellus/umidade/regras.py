"""Regras puras da umidade SMAP (spec 010): sem rede, sem relógio, sem estado global (Princípio VI).

Contrato de domínio (#53): todo valor SMAP é **contexto regional e opcional**. Ele nunca entra
num cálculo do TELLUS e nunca representa o ponto da lavoura. A grade é parametrizável porque o
produto (36 km ou 9 km) depende da decisão D-008 (#70).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

from tellus.localizacao.regras import haversine_km, ponto_em_poligono

# ---------------------------------------------------------------- contrato de contexto regional

NATUREZA = "contexto_regional"
USO = (
    "Contexto regional opcional. Este valor não entra em nenhum cálculo do TELLUS, "
    "não substitui dados da sua área e não muda o resultado principal."
)
DECISAO_PRODUTO = {
    "id": "D-008",
    "issue": "https://github.com/Pedrojscx/TELLUS/issues/70",
    "pergunta": "Qual produto SMAP e regra de período serão usados como contexto regional?",
    "estado": "decisao_pendente",
}

# Situações de um metadado (#93): nada desconhecido aparece como confirmado.
CONFIRMADO_NO_ARQUIVO = "confirmado_no_arquivo"
DOCUMENTADO = "documentado_na_ficha"
CALCULADO = "calculado_pela_regra"
HIPOTESE = "hipotese"
DESCONHECIDO = "desconhecido"
SITUACOES = {CONFIRMADO_NO_ARQUIVO, DOCUMENTADO, CALCULADO, HIPOTESE, DESCONHECIDO}

# Termos que nenhum texto da umidade pode conter (Princípio IV e edge case da spec 010).
TERMOS_PROIBIDOS = (
    "previsão", "previsao", "prever", "vai chover", "vai secar",
    "medição da fazenda", "medição da lavoura", "medicao da fazenda", "medicao da lavoura",
    "medido na lavoura", "medido na fazenda", "produtividade", "rendimento", "recomendação", "recomendacao",
)
CHAVES_PROIBIDAS = ("recomendacao", "produtividade", "rendimento", "sc_ha", "kg_ha", "decisao_plantio")

CAMPOS_ITEM = ("estado", "valor", "produto", "versao", "celula", "periodo", "unidade", "qualidade",
               "resolucao", "aviso_escala", "natureza", "uso")


def aviso_escala(resolucao_espacial: str, resolucao_temporal: str, distancia_km: float | None) -> dict:
    """Aviso de escala espacial e temporal que acompanha cada valor (FR-003, SC-001)."""
    dist = f" O centro da célula fica a {distancia_km:.1f} km do ponto informado." if distancia_km is not None else ""
    return {
        "codigo": "escala_regional",
        "espacial": (
            f"Valor médio de uma célula de satélite ({resolucao_espacial}), muito maior que um talhão: "
            "descreve a região, não o solo do seu ponto." + dist
        ),
        "temporal": (
            f"Retrato de um momento ({resolucao_temporal}); a umidade muda em horas com chuva ou sol "
            "e este valor não diz como o solo estará nos próximos dias."
        ),
    }


def metadado(valor, situacao: str, fonte: str | None = None) -> dict:
    if situacao not in SITUACOES:
        raise ValueError(f"situação de metadado inválida: {situacao}")
    if valor is None and situacao != DESCONHECIDO:
        raise ValueError("metadado sem valor precisa ser 'desconhecido'")
    return {"valor": valor, "situacao": situacao, "fonte": fonte}


def item_contexto(*, estado: str, valor: float | None, motivo: str | None, produto: dict, versao: dict,
                  celula: dict, periodo: dict, unidade: dict, qualidade: dict, resolucao: dict,
                  aviso: dict) -> dict:
    """Único construtor de um valor SMAP. Garante natureza, uso e aviso em todo item (#53, #94)."""
    if estado not in ("disponivel", "indisponivel"):
        raise ValueError(f"estado inválido: {estado}")
    if estado == "indisponivel" and (valor is not None or not motivo):
        raise ValueError("indisponível não tem valor e precisa de motivo (sem substituição)")
    if estado == "disponivel" and valor is None:
        raise ValueError("disponível precisa de valor")
    return {
        "estado": estado, "valor": valor, "motivo": motivo, "natureza": NATUREZA, "uso": USO,
        "produto": produto, "versao": versao, "celula": celula, "periodo": periodo, "unidade": unidade,
        "qualidade": qualidade, "resolucao": resolucao, "aviso_escala": aviso,
    }


def validar_item(item: Mapping) -> list[str]:
    """Lista de violações do contrato num item (vazio = válido)."""
    erros = [f"falta {c}" for c in CAMPOS_ITEM if c not in item]
    if erros:
        return erros
    if item["natureza"] != NATUREZA:
        erros.append("natureza diferente de contexto_regional")
    av = item["aviso_escala"] or {}
    if not av.get("espacial") or not av.get("temporal"):
        erros.append("aviso de escala espacial e temporal ausente")
    for campo in ("versao", "unidade"):
        m = item[campo] or {}
        if m.get("situacao") not in SITUACOES:
            erros.append(f"{campo} sem situação")
        if m.get("valor") is None and m.get("situacao") != DESCONHECIDO:
            erros.append(f"{campo} sem valor marcado como conhecido")
    if item["estado"] == "indisponivel" and item["valor"] is not None:
        erros.append("indisponível com valor (substituição)")
    return erros


def textos(obj) -> Iterable[str]:
    """Todas as strings de uma resposta (chaves e valores)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            yield str(k)
            yield from textos(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from textos(v)


def termos_proibidos(obj) -> list[str]:
    achados = []
    for t in textos(obj):
        baixo = t.lower()
        achados += [f"{termo!r} em {t[:60]!r}" for termo in TERMOS_PROIBIDOS if termo in baixo]
    return achados


def chaves(obj) -> Iterable[str]:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield str(k)
            yield from chaves(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from chaves(v)


# ---------------------------------------------------------------- EASE-Grid 2.0 global (EPSG:6933)

A_WGS84 = 6378137.0
E_WGS84 = 0.0818191908426215  # excentricidade do WGS84
LAT_TS = 30.0  # paralelo padrão do EASE-Grid 2.0 global
X0_M = 17367530.44516138  # meia largura do mapa (x em lon = 180°), conferida com pyproj
_E2 = E_WGS84 ** 2
_K0 = math.cos(math.radians(LAT_TS)) / math.sqrt(1 - _E2 * math.sin(math.radians(LAT_TS)) ** 2)


def _q(sen: float) -> float:
    return (1 - _E2) * (sen / (1 - _E2 * sen * sen) - (1 / (2 * E_WGS84)) * math.log((1 - E_WGS84 * sen) / (1 + E_WGS84 * sen)))


_QP = _q(1.0)


def ease2_xy(lat: float, lon: float) -> tuple[float, float]:
    """Coordenadas em metros na projeção cilíndrica de área igual EPSG:6933."""
    return A_WGS84 * _K0 * math.radians(lon), A_WGS84 * _q(math.sin(math.radians(lat))) / (2 * _K0)


def ease2_latlon(x: float, y: float) -> tuple[float, float]:
    """Inversa de `ease2_xy` (latitude autálica, série de Snyder 1987, eq. 3-18)."""
    beta = math.asin(max(-1.0, min(1.0, 2 * _K0 * y / (A_WGS84 * _QP))))
    e4, e6 = _E2 ** 2, _E2 ** 3
    lat = (beta + (_E2 / 3 + 31 * e4 / 180 + 517 * e6 / 5040) * math.sin(2 * beta)
           + (23 * e4 / 360 + 251 * e6 / 3780) * math.sin(4 * beta) + (761 * e6 / 45360) * math.sin(6 * beta))
    return math.degrees(lat), math.degrees(x / (A_WGS84 * _K0))


def tamanho_celula_m(colunas: int) -> float:
    return 2 * X0_M / colunas


def celula_ease2(lat: float, lon: float, colunas: int, linhas: int) -> tuple[int, int] | None:
    """(linha, coluna) da célula que contém o ponto; None fora da grade (ex.: |lat| > ~85°)."""
    cel = tamanho_celula_m(colunas)
    y0 = linhas * cel / 2
    x, y = ease2_xy(lat, lon)
    col = math.floor(round((x + X0_M) / cel, 9))
    lin = math.floor(round((y0 - y) / cel, 9))
    if col == colunas and lon == 180.0:
        col = colunas - 1
    if not (0 <= col < colunas and 0 <= lin < linhas):
        return None
    return lin, col


def centro_celula(linha: int, coluna: int, colunas: int, linhas: int) -> tuple[float, float]:
    cel = tamanho_celula_m(colunas)
    x = -X0_M + (coluna + 0.5) * cel
    y = linhas * cel / 2 - (linha + 0.5) * cel
    lat, lon = ease2_latlon(x, y)
    return round(lat, 5), round(lon, 5)


def descrever_celula(lat: float, lon: float, grade_id: str, grade: Mapping) -> dict | None:
    """Célula com índices, centro, tamanho e distância ao ponto pedido."""
    lc = celula_ease2(lat, lon, grade["colunas"], grade["linhas"])
    if lc is None:
        return None
    lin, col = lc
    clat, clon = centro_celula(lin, col, grade["colunas"], grade["linhas"])
    return {
        "grade": grade_id, "linha": lin, "coluna": col, "centro_lat": clat, "centro_lon": clon,
        "tamanho_km": round(tamanho_celula_m(grade["colunas"]) / 1000, 2),
        "distancia_km": round(haversine_km(lat, lon, clat, clon), 2),
    }


def celulas_da_geometria(geometria: dict, colunas: int, linhas: int, passo: float = 0.005) -> dict[tuple[int, int], float]:
    """Fração da área em cada célula (amostragem regular). Não faz média entre células: cada célula
    vira um item próprio, porque juntar células seria uma regra ainda não decidida."""
    tipo = geometria["type"]
    if tipo == "Point":
        lon, lat = geometria["coordinates"][:2]
        lc = celula_ease2(lat, lon, colunas, linhas)
        return {lc: 1.0} if lc else {}
    if tipo not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"geometria não suportada: {tipo}")
    aneis = [geometria["coordinates"][0]] if tipo == "Polygon" else [p[0] for p in geometria["coordinates"]]
    xs = [x for a in aneis for x, _ in a]
    ys = [y for a in aneis for _, y in a]
    n_lat = max(1, round((max(ys) - min(ys)) / passo))
    n_lon = max(1, round((max(xs) - min(xs)) / passo))
    contagem: dict[tuple[int, int], int] = {}
    for i in range(n_lat):
        lat = min(ys) + (i + 0.5) * (max(ys) - min(ys)) / n_lat
        for j in range(n_lon):
            lon = min(xs) + (j + 0.5) * (max(xs) - min(xs)) / n_lon
            if ponto_em_poligono(lat, lon, geometria):
                lc = celula_ease2(lat, lon, colunas, linhas)
                if lc:
                    contagem[lc] = contagem.get(lc, 0) + 1
    total = sum(contagem.values())
    if total == 0:
        lc = celula_ease2((min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2, colunas, linhas)
        return {lc: 1.0} if lc else {}
    return {c: round(n / total, 4) for c, n in sorted(contagem.items())}


# ---------------------------------------------------------------- valor e qualidade


def valor_valido(valor: float | None, fill: float) -> bool:
    return valor is not None and math.isfinite(valor) and valor != fill and valor >= 0


def qualidade_l3(flag: int | None, fill: int | None) -> dict:
    """Interpreta `retrieval_qual_flag` (guia NSIDC SPL3SMP_E V006, Tabela 6). Sem flag → desconhecida."""
    if flag is None or (fill is not None and flag == fill):
        return {"flag": None, "recomendada": None, "situacao": DESCONHECIDO,
                "texto": "Qualidade desconhecida: o arquivo não trouxe a flag de qualidade."}
    return {
        "flag": flag,
        "recomendada": (flag & 1) == 0,
        "tentativa": (flag & 2) == 0,
        "sucesso": (flag & 4) == 0,
        "situacao": CONFIRMADO_NO_ARQUIVO,
        "texto": ("Qualidade recomendada pela NASA (bit 0 = 0)." if (flag & 1) == 0
                  else "Sem qualidade recomendada pela NASA (bit 0 = 1): use com cautela."),
    }


def qualidade_sem_flag(nivel: str) -> dict:
    """Produtos sem flag por célula (L4): a qualidade não é inventada."""
    return {"flag": None, "recomendada": None, "situacao": DESCONHECIDO,
            "texto": f"O produto {nivel} não traz flag de qualidade por célula neste cache; qualidade desconhecida."}
