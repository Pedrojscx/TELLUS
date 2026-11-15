"""Monta o ResultadoLocalizacao (data-model.md) a partir das regras e das referências."""

from __future__ import annotations

import math

from . import regras
from .referencias import Procedencia, Referencias

# Rio Verde-GO: ponto da estação INMET A025 (REGISTRO.md), local padrão da demonstração.
PADRAO_LAT = -17.785278
PADRAO_LON = -50.965
PADRAO_CODIGO = "5218805"

MUNICIPIOS_INSULARES = {"2605459"}  # Fernando de Noronha-PE
CULTURAS_CONAB = ("soja", "milho_2a_safra", "sorgo")
NOMES_CULTURA = {"soja": "soja", "milho_2a_safra": "milho 2ª safra", "sorgo": "sorgo"}
FAIXA_COSTEIRA_KM = 50.0


class ErroLocalizacao(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


def _aviso(codigo: str, mensagem: str, referencia: str | None) -> dict:
    return {"codigo": codigo, "mensagem": mensagem, "referencia": referencia}


def _resumo(m: dict) -> dict:
    return {"codigo_ibge": m["codigo_ibge"], "nome": m["nome"], "uf": m["uf"]}


def _km(d: float) -> float:
    return round(d, 2)


def validar_coordenadas(lat, lon) -> tuple[float, float]:
    valores = []
    for nome, valor, limite in (("lat", lat, 90), ("lon", lon, 180)):
        try:
            v = float(valor)
        except (TypeError, ValueError):
            raise ErroLocalizacao("coordenada_invalida", f"{nome} precisa ser um número em graus decimais.", nome)
        if math.isnan(v) or not -limite <= v <= limite:
            raise ErroLocalizacao(
                "coordenada_invalida", f"{nome} precisa estar entre -{limite} e {limite}.", nome
            )
        valores.append(v)
    return valores[0], valores[1]


def municipio_do_ponto(ref: Referencias, lat: float, lon: float) -> tuple[dict, dict | None]:
    """Município que contém o ponto e, se houver, o vizinho a menos de `divisa_km`."""
    divisa = ref.limite("divisa_km")
    folga = divisa / 100  # ~1 km em graus, para filtrar vizinhos pelo bbox
    contem = None
    candidatos_vizinhos = []
    for cod, geom in ref.malha.items():
        m = ref.municipios.get(cod)
        if not m or not m.get("bbox") or not regras.dentro_do_bbox(lat, lon, m["bbox"], folga):
            continue
        if contem is None and regras.ponto_em_poligono(lat, lon, geom):
            contem = m
        else:
            candidatos_vizinhos.append((cod, geom, m))
    if contem is None and candidatos_vizinhos:
        # A malha mínima simplifica costas e ilhas: aceita o município mais próximo dentro da folga.
        dist, cod, m = min(
            (regras.distancia_a_geometria_km(lat, lon, g), c, mm) for c, g, mm in candidatos_vizinhos
        )
        if dist < divisa:
            return m, {"_fora_do_contorno_km": round(dist, 2), **m}
    if contem is None:
        if not regras.ponto_em_poligono(lat, lon, ref.brasil):
            perto_costa = regras.distancia_a_geometria_km(lat, lon, ref.brasil) <= FAIXA_COSTEIRA_KM
            if perto_costa:
                raise ErroLocalizacao(
                    "fora_de_municipio", "O ponto não está em nenhum município brasileiro (fica no mar)."
                )
            raise ErroLocalizacao("fora_do_brasil", "O TELLUS cobre apenas o território brasileiro.")
        raise ErroLocalizacao("fora_de_municipio", "O ponto não está em nenhum município brasileiro.")
    vizinho = None
    melhor = math.inf
    for cod, geom, m in sorted(candidatos_vizinhos, key=lambda c: c[0]):
        if cod == contem["codigo_ibge"]:
            continue
        d = regras.distancia_a_geometria_km(lat, lon, geom)
        if d < divisa and d < melhor:
            vizinho, melhor = m, d
    return contem, vizinho


def _ref_power(ref: Referencias, lat: float, lon: float) -> dict:
    clat, clon = regras.celula_power(lat, lon)
    return {
        "tipo": "celula_power",
        "identificador": f"POWER {clat:.3f},{clon:.3f}",
        "nome": None,
        "lat": clat,
        "lon": clon,
        "distancia_km": _km(regras.haversine_km(lat, lon, clat, clon)),
        "detalhes": {"passo_lat": regras.PASSO_POWER_LAT, "passo_lon": regras.PASSO_POWER_LON},
        "procedencia": Procedencia(
            fonte="NASA POWER — grade 0,5° × 0,625° (centro calculado; conferido no REGISTRO.md)",
            url="https://power.larc.nasa.gov/",
            obtido_em=ref.versao,
        ).como_dict(),
        "avisos": [],
    }


def _ref_imerg(ref: Referencias, lat: float, lon: float) -> dict:
    clat, clon = regras.celula_imerg(lat, lon)
    return {
        "tipo": "celula_imerg",
        "identificador": f"IMERG {clat:.2f},{clon:.2f}",
        "nome": None,
        "lat": clat,
        "lon": clon,
        "distancia_km": _km(regras.haversine_km(lat, lon, clat, clon)),
        "detalhes": {"passo": regras.PASSO_IMERG},
        "procedencia": Procedencia(
            fonte="NASA GPM IMERG Final — grade 0,1° (centro calculado; conferido na pesquisa de chuva)",
            url="https://gpm.nasa.gov/data/imerg",
            obtido_em=ref.versao,
        ).como_dict(),
        "avisos": [],
    }


def _ref_estacao(ref: Referencias, lat: float, lon: float) -> dict:
    proc = ref.procedencias["estacoes_inmet.json"].como_dict()
    coords = lambda e: (e["lat"], e["lon"])  # noqa: E731
    ident = lambda e: e["codigo"]  # noqa: E731
    operantes = [e for e in ref.estacoes if e["situacao"] == "Operante"]
    achado = regras.mais_proximo(lat, lon, operantes, coords, ident)
    if achado is None:
        aviso = _aviso("referencia_inexistente", "Nenhuma estação INMET operante encontrada.", "estacao_inmet")
        return {
            "tipo": "estacao_inmet", "identificador": "-", "nome": None, "lat": lat, "lon": lon,
            "distancia_km": 0.0, "detalhes": {}, "procedencia": proc, "avisos": [aviso],
        }
    est, dist = achado
    avisos = []
    limite = ref.limite("estacao_distante_km")
    if dist > limite:
        avisos.append(
            _aviso(
                "estacao_distante",
                f"A estação INMET mais próxima ({est['codigo']}, {est['nome']}) fica a {dist:.0f} km. "
                f"Acima de {limite:.0f} km a comparação local de chuva perde validade.",
                "estacao_inmet",
            )
        )
    em_pane = regras.mais_proximo(
        lat, lon, (e for e in ref.estacoes if e["situacao"] != "Operante"), coords, ident
    )
    if em_pane and em_pane[1] < dist:
        p, dp = em_pane
        avisos.append(
            _aviso(
                "estacao_em_pane_ignorada",
                f"A estação {p['codigo']} ({p['nome']}), a {dp:.0f} km, está em pane e não foi usada.",
                "estacao_inmet",
            )
        )
    return {
        "tipo": "estacao_inmet",
        "identificador": est["codigo"],
        "nome": f"{est['nome']}-{est['uf']}",
        "lat": est["lat"],
        "lon": est["lon"],
        "distancia_km": _km(dist),
        "detalhes": {
            "altitude_m": est["altitude_m"],
            "situacao": est["situacao"],
            "inicio_operacao": est["inicio_operacao"],
            "uf": est["uf"],
        },
        "procedencia": proc,
        "avisos": avisos,
    }


def _ref_praca(ref: Referencias, lat: float, lon: float, municipio: dict) -> dict:
    proc = ref.procedencias["conab_soja.xls"]
    proc = Procedencia(
        fonte="Conab — séries históricas de custos de produção (soja, milho 2ª safra, sorgo), praças de 2025/2026",
        url=proc.url.rsplit("/", 1)[0],
        obtido_em=proc.obtido_em,
    ).como_dict()
    coords = lambda p: (p["lat"], p["lon"])  # noqa: E731
    ident = lambda p: p["codigo_ibge"]  # noqa: E731
    achado = regras.mais_proximo(lat, lon, ref.pracas, coords, ident)
    if achado is None:
        aviso = _aviso("referencia_inexistente", "Nenhuma praça Conab com custo publicado.", "praca_conab")
        return {
            "tipo": "praca_conab", "identificador": "-", "nome": None, "lat": lat, "lon": lon,
            "distancia_km": 0.0, "detalhes": {}, "procedencia": proc, "avisos": [aviso],
        }
    praca, dist = achado
    por_cultura = {}
    for c in CULTURAS_CONAB:
        r = regras.mais_proximo(lat, lon, (p for p in ref.pracas if p["culturas"][c]), coords, ident)
        por_cultura[c] = (
            {"nome": f"{r[0]['nome']}-{r[0]['uf']}", "codigo_ibge": r[0]["codigo_ibge"], "distancia_km": _km(r[1])}
            if r
            else None
        )
    avisos = []
    if praca["codigo_ibge"] != municipio["codigo_ibge"]:
        avisos.append(
            _aviso(
                "praca_outro_municipio",
                f"Não há planilha de custo da Conab para {municipio['nome']}-{municipio['uf']}. "
                f"A praça mais próxima é {praca['nome']}-{praca['uf']}, a {dist:.0f} km: os custos são de outra região.",
                "praca_conab",
            )
        )
    for c, r in por_cultura.items():
        if r is None:
            avisos.append(
                _aviso("referencia_inexistente", f"Nenhuma praça Conab com custo de {NOMES_CULTURA[c]}.", "praca_conab")
            )
    return {
        "tipo": "praca_conab",
        "identificador": praca["codigo_ibge"],
        "nome": f"{praca['nome']}-{praca['uf']}",
        "lat": praca["lat"],
        "lon": praca["lon"],
        "distancia_km": _km(dist),
        "detalhes": {
            "uf": praca["uf"],
            "codigo_ibge": praca["codigo_ibge"],
            "culturas": praca["culturas"],
            "mais_proxima_por_cultura": por_cultura,
        },
        "procedencia": proc,
        "avisos": avisos,
    }


def _ref_zarc(ref: Referencias, lat: float, lon: float, municipio: dict) -> dict:
    c = municipio["centroide"]
    proc = ref.procedencias["municipios.json"]
    return {
        "tipo": "municipio_zarc",
        "identificador": municipio["codigo_ibge"],
        "nome": f"{municipio['nome']}-{municipio['uf']}",
        "lat": c["lat"],
        "lon": c["lon"],
        "distancia_km": _km(regras.haversine_km(lat, lon, c["lat"], c["lon"])),
        "detalhes": {"codigo_ibge": municipio["codigo_ibge"], "uf": municipio["uf"]},
        "procedencia": Procedencia(
            fonte="IBGE — código do município, usado na consulta ao ZARC (SISZARC/MAPA)",
            url=proc.url,
            obtido_em=proc.obtido_em,
        ).como_dict(),
        "avisos": [],
    }


def resolver(ref: Referencias, lat, lon, meio: str = "coordenadas", municipio: dict | None = None) -> dict:
    lat, lon = validar_coordenadas(lat, lon)
    vizinho = None
    if municipio is None:
        municipio, vizinho = municipio_do_ponto(ref, lat, lon)
    avisos_local = []
    if vizinho and "_fora_do_contorno_km" in vizinho:
        avisos_local.append(
            _aviso(
                "divisa_ambigua",
                f"O ponto ficou {vizinho['_fora_do_contorno_km']:.1f} km fora do contorno simplificado do IBGE; "
                f"usamos o município mais próximo, {municipio['nome']}-{municipio['uf']}.",
                None,
            )
        )
        vizinho = None
    if vizinho:
        avisos_local.append(
            _aviso(
                "divisa_ambigua",
                f"O ponto fica perto da divisa com {vizinho['nome']}-{vizinho['uf']}; "
                f"confira se a lavoura está em {municipio['nome']}-{municipio['uf']}.",
                None,
            )
        )
    if municipio["codigo_ibge"] in MUNICIPIOS_INSULARES:
        avisos_local.append(
            _aviso(
                "ilha_oceanica",
                "Ilha oceânica: podem faltar estação INMET próxima, ZARC e praça Conab.",
                None,
            )
        )
    referencias = [
        _ref_power(ref, lat, lon),
        _ref_imerg(ref, lat, lon),
        _ref_estacao(ref, lat, lon),
        _ref_praca(ref, lat, lon, municipio),
        _ref_zarc(ref, lat, lon, municipio),
    ]
    avisos = avisos_local + [a for r in referencias for a in r["avisos"]]
    return {
        "local": {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "meio": meio,
            "municipio": _resumo(municipio),
            "municipio_alternativo": _resumo(vizinho) if vizinho else None,
        },
        "referencias": referencias,
        "avisos": avisos,
        "versao_referencias": ref.versao,
        "eh_demo": meio == "padrao",
    }


def resolver_municipio(ref: Referencias, codigo_ibge: str) -> dict:
    m = ref.municipios.get(codigo_ibge)
    if m is None or not m.get("centroide"):
        raise ErroLocalizacao(
            "municipio_nao_encontrado",
            f"Município {codigo_ibge} não encontrado (ou ainda sem limite na malha do IBGE).",
            "codigo_ibge",
            status=404,
        )
    c = m["centroide"]
    return resolver(ref, c["lat"], c["lon"], meio="busca", municipio=m)


def resolver_padrao(ref: Referencias) -> dict:
    return resolver(ref, PADRAO_LAT, PADRAO_LON, meio="padrao", municipio=ref.municipios[PADRAO_CODIGO])
