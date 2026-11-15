"""Monta as entradas rastreáveis (clima 003, ZARC 004, solo e cultura 005) e roda o motor puro (spec 006)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from tellus.clima import servico as clima
from tellus.culturas import servico as culturas
from tellus.localizacao.referencias import carregar as carregar_loc
from tellus.localizacao.servico import resolver
from tellus.zarc import regras as zarc_regras
from tellus.zarc import servico as zarc

from . import balanco, eto, simulacao

RAIZ = Path(__file__).resolve().parents[4]
PREMISSAS = json.loads((RAIZ / "referencias" / "motor" / "premissas.json").read_text(encoding="utf-8"))
# cultura da base (005) → cultura do ZARC (004)
CULTURA_ZARC = {
    "milho_2a_safra": "milho_2a_safra",
    "sorgo_granifero_2a_safra": "sorgo_granifero_2a_safra",
    "braquiaria_cobertura": "milho_2a_safra_braquiaria",
}
AVISO_HISTORICO = ("Frequência histórica calculada com a série observada (IMERG e POWER), uma simulação por ano. "
                   "Não é previsão da próxima safra.")
SAFRA_ZARC_ANO = 2027  # ano de referência para o decêndio na safra 2026/2027


class ErroMotor(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def _mmdd(texto: str, campo: str) -> str:
    t = texto.strip()
    try:
        if len(t) == 10:
            return dt.date.fromisoformat(t).strftime("%m-%d")
        dt.date.fromisoformat(f"2028-{t}")
        return t
    except ValueError:
        raise ErroMotor("data_invalida", f"{campo}: use AAAA-MM-DD ou MM-DD.", campo)


def _cultura(params: dict, grupo: str | None, cultura: str) -> tuple[balanco.Cultura, str]:
    p = {x["id"]: x["valor_usado"] for x in params["parametros"]}
    fases_tab = p["fases_dias"]
    chave = grupo if grupo in fases_tab else ("UNICO" if "UNICO" in fases_tab else None)
    if chave is None:
        raise ErroMotor("grupo_invalido", f"Grupo {grupo!r} não existe para {cultura}. Use um de {sorted(fases_tab)}.", "grupo")
    ky = p.get("ky")
    isna = p.get("isna_limite", {})
    c = balanco.Cultura(
        fases=tuple(int(x) for x in fases_tab[chave]),
        kc_ini=p["kc"]["ini"], kc_med=p["kc"]["med"], kc_fim=p["kc"]["fim"],
        p=p["p_esgotamento"],
        ky_fases=None if not ky else (ky["fase_I"], ky["fase_II"], ky["fase_III"], ky["fase_IV"]),
        isna_limite_I=isna.get("fase_I"), isna_limite_III=isna.get("fase_III"),
    )
    return c, chave


def _serie_com_eto(lat: float, lon: float, geometria: dict | None = None,
                   id_geometria: str | None = None) -> tuple[list[dict], dict]:
    s = clima.serie(geometria=geometria, id_geometria=id_geometria) if geometria else clima.serie(lat, lon)
    alt = s["proveniencia"]["power"]["localizacao"].get("altitude_m") or 0.0
    dias = []
    for d in s["dias"]:
        ok = all(d[k] is not None for k in ("tmax_c", "tmin_c", "radiacao_mj_m2", "umidade_pct", "vento_m_s"))
        e = None
        if ok:
            doy = dt.date.fromisoformat(d["data"]).timetuple().tm_yday
            e = round(eto.eto(d["tmax_c"], d["tmin_c"], d["radiacao_mj_m2"], d["vento_m_s"], alt, lat, doy,
                              ur_media=d["umidade_pct"])["eto"], 3)
        dias.append({"data": d["data"], "chuva_mm": d["chuva_mm"], "eto_mm": e})
    return dias, s


def preparar(pedido: dict) -> dict:
    """Resolve e versiona todas as entradas (FR-003, SC-002). Não roda o balanço."""
    cultura = pedido.get("cultura")
    if cultura not in CULTURA_ZARC:
        raise ErroMotor("cultura_invalida", f"Cultura deve ser uma de {sorted(CULTURA_ZARC)}.", "cultura")
    lat, lon = pedido.get("lat"), pedido.get("lon")
    loc = resolver(carregar_loc(), lat, lon)
    lat, lon = loc["local"]["lat"], loc["local"]["lon"]
    ibge = pedido.get("codigo_ibge") or loc["local"]["municipio"]["codigo_ibge"]
    uf = loc["local"]["municipio"]["uf"]
    grupo = pedido.get("grupo") or "GRUPO I"
    params = culturas.premissas(cultura, uf, pedido.get("edicoes"))
    c, chave_fases = _cultura(params, grupo, cultura)
    solo_in = pedido.get("solo") or {}
    solo = culturas.classificar_solo(cultura, uf, solo_in.get("textura"), solo_in.get("granulometria"),
                                     solo_in.get("classe"), solo_in.get("cad_mm"))
    if not solo.get("cad_mm"):
        raise ErroMotor("solo_indisponivel", solo.get("aviso") or "Não foi possível obter a CAD do solo.", "solo")
    manejo = (pedido.get("entressafra") or {}).get("manejo", "palhada")
    if manejo not in PREMISSAS["entressafra"]:
        raise ErroMotor("manejo_invalido", "Entressafra deve ser 'pousio' ou 'palhada'.", "entressafra")
    ent = dict(PREMISSAS["entressafra"][manejo])
    kc_ent = (pedido.get("entressafra") or {}).get("kc")
    if kc_ent is not None:
        if not 0 <= kc_ent <= 1.2:
            raise ErroMotor("fora_do_dominio", "Kc da entressafra deve estar entre 0 e 1,2.", "entressafra.kc")
        ent |= {"kc_padrao": ent["kc"], "kc": kc_ent, "status": "editado"}
    frac = pedido.get("armazenamento_inicial_frac", PREMISSAS["estado_inicial"]["valor"])
    if not isinstance(frac, (int, float)) or not 0 <= frac <= 1:
        raise ErroMotor("fora_do_dominio", "armazenamento_inicial_frac deve estar entre 0 e 1.", "armazenamento_inicial_frac")
    colheita = _mmdd(pedido.get("data_colheita_soja") or "", "data_colheita_soja")
    if pedido.get("data_plantio"):
        plantio = _mmdd(pedido["data_plantio"], "data_plantio")
    else:
        d = dt.date.fromisoformat(f"2027-{colheita}") + dt.timedelta(days=PREMISSAS["intervalo_plantio_dias"]["valor"])
        plantio = d.strftime("%m-%d")
    estado_inicial = dict(PREMISSAS["estado_inicial"]) | {"valor": frac, "status": "editado" if frac != PREMISSAS["estado_inicial"]["valor"] else "hipotese"}
    return {
        "lat": lat, "lon": lon, "codigo_ibge": ibge, "uf": uf, "cultura": cultura, "grupo": grupo,
        "chave_fases": chave_fases, "cultura_motor": c, "params": params, "solo": solo,
        "entressafra": {"manejo": manejo, **ent}, "estado_inicial": estado_inicial,
        "colheita": colheita, "plantio": plantio, "localizacao": loc,
        "geometria": pedido.get("geometria"), "id_geometria": pedido.get("id_geometria"),
    }


def _checar_zarc(e: dict, plantio_mmdd: str) -> dict:
    """FR-002: só dentro da janela ZARC; devolve a referência da regra usada."""
    cz = CULTURA_ZARC[e["cultura"]]
    solo_zarc = e["solo"]["classe"]
    if solo_zarc is None:
        raise ErroMotor("solo_sem_classe_zarc", "A CAD informada não corresponde a uma classe do ZARC; sem classe não há janela oficial.", "solo")
    data = f"{SAFRA_ZARC_ANO}-{plantio_mmdd}"
    r = zarc.consultar_data(e["codigo_ibge"], cz, data, e["grupo"], solo_zarc)
    if not r.get("disponivel"):
        raise ErroMotor("zarc_indisponivel", r.get("motivo", "ZARC indisponível para esta combinação."), "zarc", 409)
    res = r["resultados"][0] if r["resultados"] else None
    ref = {"cultura_zarc": cz, "grupo": e["grupo"], "solo": solo_zarc, "decendio": zarc_regras.decendio(dt.date.fromisoformat(data)),
           "portaria": res["portaria"] if res else None, "safra": r["safra"], "risco_zarc_pct": res["risco_zarc_pct"] if res else None,
           "dentro_da_janela": bool(res and res["dentro_da_janela"]),
           "nota": "cobertura com braquiária usa o ZARC de milho 2ª safra com braquiária (referência mais próxima)" if e["cultura"] == "braquiaria_cobertura" else None}
    return ref


def simular(pedido: dict) -> dict:
    e = preparar(pedido)
    ref_zarc = _checar_zarc(e, e["plantio"])
    if not ref_zarc["dentro_da_janela"]:
        raise ErroMotor("fora_da_janela_zarc",
                        f"Plantio em {e['plantio']} (decêndio {ref_zarc['decendio']}) está fora da janela do ZARC "
                        f"(portaria {ref_zarc['portaria']}) para {e['cultura']}, {e['grupo']}, solo {ref_zarc['solo']}.", "data_plantio")
    dias, serie = _serie_com_eto(e["lat"], e["lon"], e["geometria"], e["id_geometria"])
    sim = simulacao.simular(dias, e["cultura_motor"], e["solo"]["cad_mm"], e["colheita"], e["plantio"],
                            e["entressafra"]["kc"], e["estado_inicial"]["valor"])
    entradas = {
        "clima": {"proveniencia": serie["proveniencia"], "origem_dados": serie["origem_dados"],
                  "ultimo_dia_publicado_imerg": serie["ultimo_dia_publicado_imerg"], "hash": _hash(dias),
                  "eto": "FAO-56 Penman-Monteith diária com variáveis do POWER (UR média, eq. 19), altitude da célula POWER"},
        "solo": e["solo"] | {"hash": _hash(e["solo"])},
        "cultura": {"cultura": e["cultura"], "grupo": e["grupo"], "fases_usadas": e["chave_fases"], "parametros": e["params"]["parametros"],
                    "alteracoes": e["params"]["alteracoes"], "hash": _hash(e["params"]["parametros"])},
        "estado_inicial": e["estado_inicial"] | {"hash": _hash(e["estado_inicial"])},
        "entressafra": e["entressafra"] | {"inicio": e["colheita"], "fim_vespera_de": e["plantio"], "hash": _hash(e["entressafra"])},
        "zarc": ref_zarc,
    }
    hipoteses = [p["nome"] for p in e["params"]["parametros"] if p["status"] == "hipotese"]
    if e["solo"]["status"] == "hipotese":
        hipoteses.append("Classe de solo estimada pela textura")
    if e["estado_inicial"]["status"] == "hipotese":
        hipoteses.append(e["estado_inicial"]["nome"])
    if e["entressafra"].get("status") == "hipotese":
        hipoteses.append(f"Kc da entressafra ({e['entressafra']['manejo']})")
    avisos = [{"codigo": "nao_e_previsao", "mensagem": AVISO_HISTORICO}]
    avisos += [a for a in serie["avisos"] if a["codigo"] != "lacuna_imerg"]
    if sim["anos_excluidos"]:
        avisos.append({"codigo": "anos_excluidos", "mensagem": f"{len(sim['anos_excluidos'])} ano(s) fora do cálculo; veja anos_excluidos."})
    if sim["anos_validos"] < 10:
        avisos.append({"codigo": "amostra_pequena", "mensagem": f"Só {sim['anos_validos']} anos válidos."})
    if hipoteses:
        avisos.append({"codigo": "hipoteses", "mensagem": "O resultado usa hipóteses: " + "; ".join(hipoteses) + "."})
    return {
        "pedido": {"cultura": e["cultura"], "grupo": e["grupo"], "codigo_ibge": e["codigo_ibge"], "lat": e["lat"], "lon": e["lon"],
                   "data_colheita_soja": e["colheita"], "data_plantio": e["plantio"]},
        "resultado": {
            "risco_historico_falha_severa": sim["risco_historico"],
            "definicao_falha": "ISNA (ETa/ETc) da fase I ou III abaixo ou igual ao limite da portaria ZARC (ou hipótese, na cobertura)",
            "anos_validos": sim["anos_validos"],
            "anos_com_falha": sim["anos_com_falha"],
            "deficit_mm_mediano": sim["deficit_mm_mediano"],
            "perda_relativa_quantis": sim["perda_relativa_quantis"],
            "risco_zarc_pct": ref_zarc["risco_zarc_pct"],
            "significado_riscos": "risco_historico_falha_severa é calculado pelo TELLUS com a série histórica; risco_zarc_pct é o risco oficial da portaria. São medidas distintas.",
        },
        "por_ano": sim["por_ano"],
        "anos_excluidos": sim["anos_excluidos"],
        "entradas": entradas,
        "versao_entradas": _hash({k: v.get("hash") for k, v in entradas.items() if isinstance(v, dict)}),
        "premissa_chuva": "Chuva do IMERG toda efetiva (sem escoamento superficial); drenagem além da capacidade de campo.",
        "avisos": avisos,
    }


def simular_janela(pedido: dict) -> dict:
    """Risco por decêndio dentro da janela ZARC (para a recomendação, 008). Plantio no 1º dia do decêndio."""
    e = preparar(pedido)
    cz = CULTURA_ZARC[e["cultura"]]
    cal = zarc.calendario(e["codigo_ibge"], cz, e["grupo"], e["solo"]["classe"])
    if not cal["disponivel"] or not cal["grupos"] or not cal["grupos"][0].get("disponivel"):
        raise ErroMotor("zarc_indisponivel", cal.get("motivo") or "ZARC indisponível para esta combinação.", "zarc", 409)
    janela = cal["grupos"][0]["solos"][0]["janela"] if cal["grupos"][0]["solos"] else []
    dias, serie = _serie_com_eto(e["lat"], e["lon"], e["geometria"], e["id_geometria"])
    colheita = dt.date.fromisoformat(f"{SAFRA_ZARC_ANO}-{e['colheita']}")
    linhas = []
    for j in janela:
        ini, _ = zarc_regras.periodo_decendio(j["decendio"], SAFRA_ZARC_ANO)
        if ini < colheita:
            ini = colheita  # não planta antes de colher; usa a própria data de colheita no decêndio dela
            if zarc_regras.decendio(ini) != j["decendio"]:
                linhas.append({"decendio": j["decendio"], "risco_zarc_pct": j["risco_zarc_pct"], "situacao": "antes_da_colheita"})
                continue
        sim = simulacao.simular(dias, e["cultura_motor"], e["solo"]["cad_mm"], e["colheita"], ini.strftime("%m-%d"),
                                e["entressafra"]["kc"], e["estado_inicial"]["valor"])
        linhas.append({"decendio": j["decendio"], "data_plantio": ini.strftime("%m-%d"), "risco_zarc_pct": j["risco_zarc_pct"],
                       "situacao": "simulado", "risco_historico_falha_severa": sim["risco_historico"],
                       "anos_validos": sim["anos_validos"], "deficit_mm_mediano": sim["deficit_mm_mediano"],
                       "perda_relativa_quantis": sim["perda_relativa_quantis"]})
    return {"cultura": e["cultura"], "grupo": e["grupo"], "codigo_ibge": e["codigo_ibge"], "solo": e["solo"],
            "data_colheita_soja": e["colheita"], "portaria": cal["grupos"][0]["proveniencia"]["portaria"],
            "decendios": linhas, "avisos": [{"codigo": "nao_e_previsao", "mensagem": AVISO_HISTORICO}]}
