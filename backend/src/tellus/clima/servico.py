"""Monta a série climática, o resumo e a validação local (data-model.md da spec 003)."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
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
PASSO_AMOSTRA = 0.005  # graus; amostragem da fração de área por célula (regras.pesos_celulas)
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


def _referencias() -> list[tuple[dict, Path]]:
    if not DIR_REF.exists():
        return []
    return [(json.loads(m.read_text(encoding="utf-8")), m.parent) for m in sorted(DIR_REF.glob("*/meta.json"))]


def _ref_imerg(chave: str) -> dict[str, dict] | None:
    """Série IMERG versionada (referencias/clima/<local>/) da MESMA célula, ou None."""
    for meta, pasta in _referencias():
        if (meta.get("imerg") or {}).get("celula") != chave:
            continue
        esperado = meta["imerg"].get("sha256_serie")
        if esperado and hashlib.sha256((pasta / "serie_diaria.csv").read_bytes()).hexdigest() != esperado:
            continue  # série versionada alterada: não usa
        linhas = {}
        with (pasta / "serie_diaria.csv").open(encoding="utf-8", newline="") as f:
            for l in csv.DictReader(f):
                linhas[l["data"]] = {"data": l["data"], "chuva_mm": l["chuva_mm"], "contagem": l["imerg_contagem"],
                                     "situacao": l["imerg_situacao"], "obtido_em": meta["imerg"]["obtido_em"]}
        return linhas
    return None


def _ref_power(chave: str) -> dict | None:
    """Série POWER versionada da MESMA célula POWER, ou None."""
    for meta, pasta in _referencias():
        if (meta.get("power") or {}).get("celula") != chave:
            continue
        dias = {}
        with (pasta / "serie_diaria.csv").open(encoding="utf-8", newline="") as f:
            for l in csv.DictReader(f):
                if l["tmax_c"] != "" or l["power_chuva_mm"] != "":
                    dias[l["data"]] = {MAPA_POWER[k]: (float(l[k]) if l[k] != "" else None) for k in MAPA_POWER} | {
                        "PRECTOTCORR": float(l["power_chuva_mm"]) if l["power_chuva_mm"] != "" else None}
        return {"dias": dias, "altitude_m": meta["power"]["altitude_m"], "fontes": meta["power"]["fontes"],
                "obtido_em": meta["power"]["obtido_em"], "url": meta["power"]["url"]}
    return None


def _carregar_imerg(cel: imerg.CelulaImerg, dir_cache: Path) -> tuple[dict[str, dict], str] | None:
    linhas = imerg.ler_cache(dir_cache, cel)
    if linhas:
        return linhas, "cache"
    ref = _ref_imerg(cel.chave)
    return (ref, "referencia_versionada") if ref else None


def _carregar_power(lat: float, lon: float, dir_cache: Path) -> tuple[dict, str, str] | None:
    chave_p, _, _ = power.chave_celula(lat, lon)
    p = power.arquivo_cache(dir_cache, lat, lon)
    if p.exists():
        return power.ler(p), "cache", chave_p
    ref = _ref_power(chave_p)
    return (ref, "referencia_versionada", chave_p) if ref else None


def _carregar_area(pesos: dict[tuple[int, int], float], lat: float, lon: float, dir_cache: Path) -> tuple[dict, dict, str, str]:
    """IMERG de cada célula com peso > 0 e POWER do ponto de referência. Falta qualquer célula → erro.

    Uma célula sem série alguma não pode ser renormalizada fora da conta: a área inteira fica sem chuva,
    com erro que nomeia as células que faltam.
    """
    celulas, faltam_cel = {}, []
    for (i_lat, i_lon), w in sorted(pesos.items()):
        if w <= 0:
            continue
        cel = imerg.CelulaImerg(i_lat, i_lon)
        lido = _carregar_imerg(cel, dir_cache)
        if lido is None:
            faltam_cel.append(cel.chave)
        else:
            celulas[(i_lat, i_lon)] = {"celula": cel, "linhas": lido[0], "origem": lido[1]}
    pw = _carregar_power(lat, lon, dir_cache)
    if faltam_cel or pw is None:
        faltam = []
        if faltam_cel:
            faltam.append("NASA GPM IMERG Final")
        if pw is None:
            faltam.append("NASA POWER")
        detalhe = f" Células IMERG sem dado guardado: {', '.join(faltam_cel)}." if faltam_cel else ""
        raise ErroClima(
            "sem_cache",
            "Não há dados de clima guardados para este local. Rode os scripts de preparação "
            "(scripts/baixar_imerg.py e scripts/baixar_power.py) com internet." + detalhe,
            " e ".join(faltam),
        )
    origens = {c["origem"] for c in celulas.values()} | {pw[1]}
    return celulas, pw[0], pw[2], "+".join(sorted(origens))


def _carregar(lat: float, lon: float, dir_cache: Path) -> tuple[dict, dict, dict, str]:
    """Ponto: uma célula IMERG, peso 1 (usado pela validação local)."""
    pesos = regras.pesos_celulas({"type": "Point", "coordinates": [lon, lat]})
    celulas, pw, chave_p, origem = _carregar_area(pesos, lat, lon, dir_cache)
    (c,) = celulas.values()
    return {"celula": c["celula"], "pesos": pesos, "linhas": c["linhas"]}, pw, {"chave_power": chave_p}, origem


def _area_do_pedido(lat, lon, geometria: dict | None, id_geometria: str | None) -> dict:
    """Ponto validado, ou geometria confirmada (mesmo id_geometria da confirmação da spec 002/CAR)."""
    if geometria is None:
        lat, lon = validar_coordenadas(lat, lon)
        return {"tipo": "ponto", "lat": lat, "lon": lon,
                "pesos": regras.pesos_celulas({"type": "Point", "coordinates": [lon, lat]})}
    from tellus.car import regras as regras_car
    from tellus.car.servico import CASAS as CASAS_ID, MAX_VERTICES  # referencias/car/limites.json

    erros = regras_car.validar_poligono(geometria, MAX_VERTICES)
    if erros:
        raise ErroClima("geometria_invalida", "Geometria inválida: " + "; ".join(erros), "pedido", 422)
    can = regras_car.canonica(geometria, CASAS_ID)
    ident = regras_car.id_geometria(can, CASAS_ID)
    if id_geometria != ident:
        raise ErroClima("geometria_nao_confirmada", "A geometria precisa vir com o id_geometria da confirmação. "
                        "Confirme a área antes de pedir a chuva.", "pedido", 422)
    c_lat, c_lon = regras_car.centroide_bbox(can)
    return {"tipo": "geometria", "lat": round(c_lat, 6), "lon": round(c_lon, 6), "id_geometria": ident,
            "area_ha": round(regras_car.area_ha(can), 2), "pesos": regras.pesos_celulas(can, PASSO_AMOSTRA)}


# ---------------------------------------------------------------- série


def serie(lat=None, lon=None, inicio: str | None = None, fim: str | None = None, dir_cache: Path | None = None,
          geometria: dict | None = None, id_geometria: str | None = None) -> dict:
    """Série diária. Ponto: uma célula IMERG (peso 1). Geometria confirmada: média ponderada pela fração
    da área em cada célula de 0,1° (regras.pesos_celulas). Se uma célula com peso > 0 não tem valor num
    dia, o dia inteiro fica sem chuva (None), com aviso; nunca há renormalização nem zero."""
    area = _area_do_pedido(lat, lon, geometria, id_geometria)
    lat, lon, pesos = area["lat"], area["lon"], area["pesos"]
    dir_cache = dir_cache or DIR_CACHE
    celulas, pw, chave_p, origem = _carregar_area(pesos, lat, lon, dir_cache)
    publicados_por_cel = [
        {d for d, l in c["linhas"].items() if l["situacao"] in ("ok", "sem_dado")} for c in celulas.values()
    ]
    publicados = sorted(set.intersection(*publicados_por_cel)) if publicados_por_cel else []
    if not publicados:
        raise ErroClima("sem_cache", "O cache do IMERG não tem nenhum dia publicado em comum nas células da área.",
                        "NASA GPM IMERG Final")
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
    varias = len(celulas) > 1
    dias = []
    n_validos = n_ausentes = 0
    contagens = []
    por_cel = {k: {"validos": 0, "sem_dado": 0, "contagens": []} for k in celulas}
    dias_parciais: list[str] = []
    d = dt.date.fromisoformat(ini)
    fim_d = dt.date.fromisoformat(fim_ef)
    while d <= fim_d:
        k = d.isoformat()
        valores: dict[tuple[int, int], float | None] = {}
        for ck, c in celulas.items():
            l = c["linhas"].get(k)
            v = float(l["chuva_mm"]) if l and l["situacao"] == "ok" and l["chuva_mm"] != "" else None
            valores[ck] = v
            if v is None:
                por_cel[ck]["sem_dado"] += 1
            else:
                por_cel[ck]["validos"] += 1
                if l.get("contagem"):
                    por_cel[ck]["contagens"].append(float(l["contagem"]))
        chuva = regras.chuva_ponderada(valores, pesos)
        if chuva is None:
            n_ausentes += 1
        else:
            n_validos += 1
            if not varias:
                (l,) = (c["linhas"].get(k) for c in celulas.values())
                if l.get("contagem"):
                    contagens.append(float(l["contagem"]))
        p = pw["dias"].get(k, {})
        item = {"data": k, "chuva_mm": None if chuva is None else round(chuva, 3)}
        if varias and chuva is None:
            sem = [celulas[ck]["celula"].chave for ck, v in valores.items() if v is None]
            item["celulas_sem_dado"] = sem
            if len(sem) < len(celulas):
                dias_parciais.append(k)
        dias.append(item | {campo: p.get(nome) for campo, nome in MAPA_POWER.items()})
        d += dt.timedelta(days=1)
    if varias and n_ausentes:
        exemplos = ", ".join(dias_parciais[:5]) + (" …" if len(dias_parciais) > 5 else "")
        avisos.append(_aviso(
            "dia_indisponivel_celula",
            f"{n_ausentes} dia(s) sem chuva da área porque ao menos uma célula IMERG não tem valor"
            + (f" ({len(dias_parciais)} com outras células válidas: {exemplos})" if dias_parciais else "")
            + ". A média não é recalculada só com as células restantes nem vira zero.",
        ))
    nao_publicados = len({d for c in celulas.values() for d, l in c["linhas"].items() if l["situacao"] == "nao_publicado"})
    plat, plon = (float(x) for x in chave_p.split("_"))
    obtido_imerg = max(
        (l.get("obtido_em") or "") for c in celulas.values() for l in c["linhas"].values()
    ) or None
    lista_cel = []
    for ck, c in celulas.items():
        cel: imerg.CelulaImerg = c["celula"]
        clat, clon = cel.centro
        q = por_cel[ck]
        lista_cel.append({
            "chave": cel.chave, "centro_lat": clat, "centro_lon": clon, "peso": round(pesos[ck], 6),
            "limites": {"lat": [round(clat - 0.05, 4), round(clat + 0.05, 4)], "lon": [round(clon - 0.05, 4), round(clon + 0.05, 4)]},
            "distancia_km": round(haversine_km(lat, lon, clat, clon), 2),
            "origem_dados": c["origem"],
            "obtido_em": max((l.get("obtido_em") or "") for l in c["linhas"].values()) or None,
            "qualidade": {"dias_validos": q["validos"], "dias_sem_dado": q["sem_dado"],
                          "contagem_media": round(sum(q["contagens"]) / len(q["contagens"]), 1) if q["contagens"] else None},
        })
    if varias:  # contagem média sobre as amostras de todas as células, nos dias com valor
        contagens = [x for q in por_cel.values() for x in q["contagens"]]
    if area["tipo"] == "ponto":
        # Ponto: proveniência idêntica à de antes da #35 (contrato 011 gravado e motor dependem dela).
        localizacao = {"celulas": [{k: c[k] for k in ("centro_lat", "centro_lon", "peso")} for c in lista_cel],
                       "distancia_km": lista_cel[0]["distancia_km"]}
    else:
        localizacao = {"tipo": "geometria", "celulas": lista_cel}
    if area["tipo"] == "geometria":
        localizacao |= {
            "id_geometria": area["id_geometria"], "area_ha": area["area_ha"],
            "soma_pesos": round(sum(c["peso"] for c in lista_cel), 6),
            "metodo": (f"fração da área em cada célula IMERG de 0,1°, por amostragem regular de {PASSO_AMOSTRA}° "
                       "dentro do polígono (tellus.clima.regras.pesos_celulas)"),
            "referencia": {"lat": lat, "lon": lon, "nota": "centro do retângulo envolvente; usado para a célula POWER"},
        }
    prov_chuva = {
        "fonte": "NASA GPM IMERG Final (precipitação diária)",
        "versao": f"{imerg.PRODUTO} {imerg.VERSAO}",
        "periodo": {"inicio": ini, "fim": fim_ef} | (
            {"fuso": "UTC (dia IMERG de 00:00 a 23:59:59 UTC)"} if area["tipo"] == "geometria" else {}),
        "unidade": {"chuva_mm": "mm/dia"},
        "localizacao": localizacao,
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
    local = {"lat": lat, "lon": lon} | ({"tipo": "geometria", "id_geometria": area["id_geometria"], "area_ha": area["area_ha"]}
                                        if area["tipo"] == "geometria" else {})
    return {
        "local": local,
        "dias": dias,
        "proveniencia": {"chuva": prov_chuva, "power": prov_power},
        "ultimo_dia_publicado_imerg": ultimo_imerg,
        "avisos": avisos,
        "origem_dados": origem,
        "versao_cache": max(filter(None, [obtido_imerg, pw.get("obtido_em")]), default=None),
    }


def resumo(lat=None, lon=None, dir_cache: Path | None = None, geometria: dict | None = None,
           id_geometria: str | None = None) -> dict:
    s = serie(lat, lon, dir_cache=dir_cache, geometria=geometria, id_geometria=id_geometria)
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
