"""Monta a série climática, o resumo e a validação local (data-model.md da spec 003)."""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path

from tellus.localizacao.regras import haversine_km
from tellus.localizacao.servico import validar_coordenadas

from . import imerg, power, regras

RAIZ = Path(__file__).resolve().parents[4]
DIR_CACHE = Path(os.environ.get("TELLUS_CACHE_CLIMA", RAIZ / "data" / "raw" / "clima"))
DIR_REF = RAIZ / "referencias" / "clima"
INMET_A025 = RAIZ / "data" / "processed" / "pesquisa_chuva" / "daily_all_sources.csv"
A025 = {"codigo": "A025", "nome": "RIO VERDE-GO", "lat": -17.78527777, "lon": -50.965}

AVISO_ESCALA = (
    "Valores de grade de satélite e reanálise representam a média de uma célula de quilômetros, "
    "não a lavoura. Frequência histórica não é previsão."
)
UNIDADES_POWER = {
    "tmax_c": "°C", "tmin_c": "°C", "radiacao_mj_m2": "MJ/m²/dia", "umidade_pct": "%", "vento_m_s": "m/s",
}
MAPA_POWER = {
    "tmax_c": "T2M_MAX", "tmin_c": "T2M_MIN", "radiacao_mj_m2": "ALLSKY_SFC_SW_DWN",
    "umidade_pct": "RH2M", "vento_m_s": "WS2M",
}


class ErroClima(Exception):
    def __init__(self, codigo: str, mensagem: str, origem: str, status: int = 404):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.origem, self.status = codigo, mensagem, origem, status


def _aviso(codigo: str, mensagem: str) -> dict:
    return {"codigo": codigo, "mensagem": mensagem}


# ---------------------------------------------------------------- carga de dados


def _referencia_versionada(chave_imerg: str, chave_power: str) -> tuple[dict, dict] | None:
    """Série exportada (ex.: Rio Verde-GO) quando as células batem com as do pedido."""
    if not DIR_REF.exists():
        return None
    for meta_p in DIR_REF.glob("*/meta.json"):
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        if meta["imerg"]["celula"] == chave_imerg and meta["power"]["celula"] == chave_power:
            imerg_l, power_d = {}, {}
            with (meta_p.parent / "serie_diaria.csv").open(encoding="utf-8", newline="") as f:
                for linha in csv.DictReader(f):
                    imerg_l[linha["data"]] = {
                        "data": linha["data"], "chuva_mm": linha["chuva_mm"],
                        "contagem": linha["imerg_contagem"], "situacao": linha["imerg_situacao"],
                        "obtido_em": meta["imerg"]["obtido_em"],
                    }
                    if linha["tmax_c"] != "" or linha["power_chuva_mm"] != "":
                        power_d[linha["data"]] = {
                            MAPA_POWER[k]: (float(linha[k]) if linha[k] != "" else None) for k in MAPA_POWER
                        } | {"PRECTOTCORR": float(linha["power_chuva_mm"]) if linha["power_chuva_mm"] != "" else None}
            power_info = {
                "dias": power_d, "altitude_m": meta["power"]["altitude_m"], "fontes": meta["power"]["fontes"],
                "obtido_em": meta["power"]["obtido_em"], "url": meta["power"]["url"],
            }
            return imerg_l, power_info
    return None


def _carregar(lat: float, lon: float, dir_cache: Path) -> tuple[dict, dict, dict, str]:
    pesos = regras.pesos_celulas({"type": "Point", "coordinates": [lon, lat]})
    (i_lat, i_lon), = pesos.keys()
    cel = imerg.CelulaImerg(i_lat, i_lon)
    chave_p, _, _ = power.chave_celula(lat, lon)
    imerg_l = imerg.ler_cache(dir_cache, cel)
    p_power = power.arquivo_cache(dir_cache, lat, lon)
    power_info = power.ler(p_power) if p_power.exists() else None
    origem = "cache"
    if not imerg_l or power_info is None:
        ref = _referencia_versionada(cel.chave, chave_p)
        if ref is None:
            faltam = [n for n, ok in (("NASA GPM IMERG Final", bool(imerg_l)), ("NASA POWER", power_info is not None)) if not ok]
            raise ErroClima(
                "sem_cache",
                "Não há dados de clima guardados para este local. Rode os scripts de preparação "
                "(scripts/baixar_imerg.py e scripts/baixar_power.py) com internet.",
                " e ".join(faltam),
            )
        imerg_l, power_info = ref
        origem = "referencia_versionada"
    return {"celula": cel, "pesos": {(i_lat, i_lon): 1.0}, "linhas": imerg_l}, power_info, {"chave_power": chave_p}, origem


# ---------------------------------------------------------------- série


def serie(lat, lon, inicio: str | None = None, fim: str | None = None, dir_cache: Path | None = None) -> dict:
    lat, lon = validar_coordenadas(lat, lon)
    dir_cache = dir_cache or DIR_CACHE
    im, pw, extra, origem = _carregar(lat, lon, dir_cache)
    cel: imerg.CelulaImerg = im["celula"]
    linhas = im["linhas"]
    publicados = sorted(d for d, l in linhas.items() if l["situacao"] in ("ok", "sem_dado"))
    if not publicados:
        raise ErroClima("sem_cache", "O cache do IMERG não tem nenhum dia publicado.", "NASA GPM IMERG Final")
    ultimo_imerg = publicados[-1]
    dias_power = sorted(pw["dias"])
    ini = max(inicio or publicados[0], publicados[0], dias_power[0])
    fim_pedido = fim or ultimo_imerg
    fim_ef = min(fim_pedido, ultimo_imerg, dias_power[-1])
    avisos = [_aviso("escala_regional", AVISO_ESCALA)]
    if fim_pedido > ultimo_imerg:
        avisos.append(
            _aviso(
                "lacuna_imerg",
                f"O IMERG Final publicado termina em {ultimo_imerg}; o período pedido até {fim_pedido} "
                "foi cortado. Nenhuma outra fonte substitui a chuva.",
            )
        )
    dias = []
    n_validos = n_ausentes = 0
    contagens = []
    d = dt.date.fromisoformat(ini)
    fim_d = dt.date.fromisoformat(fim_ef)
    while d <= fim_d:
        k = d.isoformat()
        l = linhas.get(k)
        valor = float(l["chuva_mm"]) if l and l["situacao"] == "ok" and l["chuva_mm"] != "" else None
        chuva = regras.chuva_ponderada({(cel.i_lat, cel.i_lon): valor}, im["pesos"])
        if chuva is None:
            n_ausentes += 1
        else:
            n_validos += 1
            if l.get("contagem"):
                contagens.append(float(l["contagem"]))
        p = pw["dias"].get(k, {})
        dias.append({"data": k, "chuva_mm": None if chuva is None else round(chuva, 3)}
                    | {campo: p.get(nome) for campo, nome in MAPA_POWER.items()})
        d += dt.timedelta(days=1)
    nao_publicados = sum(1 for l in linhas.values() if l["situacao"] == "nao_publicado")
    clat, clon = cel.centro
    plat, plon = (float(x) for x in extra["chave_power"].split("_"))
    obtido_imerg = max((l.get("obtido_em") or "") for l in linhas.values()) or None
    prov_chuva = {
        "fonte": "NASA GPM IMERG Final (precipitação diária)",
        "versao": f"{imerg.PRODUTO} {imerg.VERSAO}",
        "periodo": {"inicio": ini, "fim": fim_ef},
        "unidade": {"chuva_mm": "mm/dia"},
        "localizacao": {"celulas": [{"centro_lat": clat, "centro_lon": clon, "peso": 1.0}],
                        "distancia_km": round(haversine_km(lat, lon, clat, clon), 2)},
        "qualidade": {"dias_validos": n_validos, "dias_ausentes": n_ausentes, "dias_nao_publicados": nao_publicados,
                      "contagem_media": round(sum(contagens) / len(contagens), 1) if contagens else None},
        "resolucao": "0,1° × 0,1° (≈ 11 km), diária (UTC)",
        "aviso_escala": AVISO_ESCALA,
        "obtido_em": obtido_imerg,
        "url": imerg.BASE,
    }
    validos_power = sum(1 for x in dias if x["tmax_c"] is not None and x["radiacao_mj_m2"] is not None)
    prov_power = {
        "fonte": "NASA POWER (variáveis diárias para ETo)",
        "versao": "POWER daily, community AG (" + ", ".join(pw.get("fontes") or []) + ")",
        "periodo": {"inicio": ini, "fim": fim_ef},
        "unidade": UNIDADES_POWER,
        "localizacao": {"centro_lat": plat, "centro_lon": plon, "altitude_m": pw.get("altitude_m"),
                        "distancia_km": round(haversine_km(lat, lon, plat, plon), 2)},
        "qualidade": {"dias_validos": validos_power, "dias_ausentes": len(dias) - validos_power},
        "resolucao": "0,5° × 0,625° (≈ 55 km), diária (UTC)",
        "aviso_escala": AVISO_ESCALA,
        "obtido_em": pw.get("obtido_em"),
        "url": power.URL,
    }
    return {
        "local": {"lat": lat, "lon": lon},
        "dias": dias,
        "proveniencia": {"chuva": prov_chuva, "power": prov_power},
        "ultimo_dia_publicado_imerg": ultimo_imerg,
        "avisos": avisos,
        "origem_dados": origem,
        "versao_cache": max(filter(None, [obtido_imerg, pw.get("obtido_em")]), default=None),
    }


def resumo(lat, lon, dir_cache: Path | None = None) -> dict:
    s = serie(lat, lon, dir_cache=dir_cache)
    por_ano: dict[str, dict] = {}
    for d in s["dias"]:
        a = por_ano.setdefault(d["data"][:4], {"ano": int(d["data"][:4]), "dias": 0, "chuva_validos": 0, "chuva_mm": 0.0})
        a["dias"] += 1
        if d["chuva_mm"] is not None:
            a["chuva_validos"] += 1
            a["chuva_mm"] += d["chuva_mm"]
    cobertura = [a | {"chuva_mm": round(a["chuva_mm"], 1)} for a in sorted(por_ano.values(), key=lambda x: x["ano"])]
    return {k: s[k] for k in ("local", "proveniencia", "ultimo_dia_publicado_imerg", "avisos", "origem_dados", "versao_cache")} | {
        "cobertura_por_ano": cobertura
    }


# ---------------------------------------------------------------- validação local


def validacao(lat, lon, recorte: str = "jan-jun", dir_cache: Path | None = None) -> dict:
    from tellus.localizacao.referencias import carregar as carregar_loc
    from tellus.localizacao.servico import resolver

    lat, lon = validar_coordenadas(lat, lon)
    loc = resolver(carregar_loc(), lat, lon)
    est = next(r for r in loc["referencias"] if r["tipo"] == "estacao_inmet")
    base = {"estacao": {"codigo": est["identificador"], "nome": est["nome"], "distancia_km": est["distancia_km"]},
            "recorte": recorte}
    if est["identificador"] != A025["codigo"] or not INMET_A025.exists():
        return base | {"disponivel": False,
                       "motivo": "Série diária validada só existe para a estação A025 (Rio Verde-GO). A API de dados do "
                                 "INMET não está aberta; para outras estações é preciso preparar os arquivos anuais do portal."}
    dir_cache = dir_cache or DIR_CACHE
    # chuva sempre no ponto da estação (célula da estação), como na pesquisa
    s = serie(A025["lat"], A025["lon"], dir_cache=dir_cache)
    imerg_por_dia = {d["data"]: d["chuva_mm"] for d in s["dias"]}
    _, pw, _, _ = _carregar(A025["lat"], A025["lon"], dir_cache)
    ref, im, pwc, excl = [], [], [], {"sem_par_inmet": 0, "imerg_ausente": 0, "power_ausente": 0}
    datas = []
    with INMET_A025.open(encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            mes = int(linha["month"])
            if recorte == "jan-jun" and mes > 6:
                continue
            if linha["paired"] != "True" or linha["inmet"] == "":
                excl["sem_par_inmet"] += 1
                continue
            vi = imerg_por_dia.get(linha["date"])
            vp = pw["dias"].get(linha["date"], {}).get("PRECTOTCORR")
            if vi is None:
                excl["imerg_ausente"] += 1
                continue
            if vp is None:
                excl["power_ausente"] += 1
                continue
            datas.append(linha["date"])
            ref.append(float(linha["inmet"]))
            im.append(vi)
            pwc.append(vp)
    if not ref:
        return base | {"disponivel": False, "motivo": "Nenhum dia pareado entre a estação e o cache de satélite."}
    return base | {
        "disponivel": True,
        "periodo": {"inicio": min(datas), "fim": max(datas), "anos": sorted({d[:4] for d in datas})},
        "dias_pareados": len(ref),
        "dias_excluidos": excl,
        "metricas": {"imerg": regras.metricas(ref, im), "power_chuva": regras.metricas(ref, pwc)},
        "fonte_estacao": {
            "fonte": "INMET, estação automática A025 (soma diária de 24 horas válidas)",
            "arquivo": "data/processed/pesquisa_chuva/daily_all_sources.csv",
            "metodo": "docs/pesquisa_chuva/RELATORIO.md",
        },
        "nota": "A chuva do POWER aparece só nesta comparação; ela nunca entra no cálculo.",
    }
