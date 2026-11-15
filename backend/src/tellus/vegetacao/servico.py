"""Contexto histórico de vegetação (spec 009): MODIS MOD13Q1/MYD13Q1 v061 e HLS v2.0.

Lê só o cache local (data/raw/vegetacao/<chave_area>/), recriado por scripts/preparar_vegetacao.py.
Cada observação e cada indicador levam produto, versão, período, resolução, unidade, qualidade,
área, aviso de escala e limitação. Dado sem qualidade vira lacuna (valor null + motivo). HLS
indisponível (sem credencial ou sem cache) não impede o MODIS. Nenhum valor é convertido em
colheita: isto é contexto, não estimativa.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path

from tellus.car import regras as regras_car
from tellus.localizacao.servico import validar_coordenadas

from . import regras

RAIZ = Path(__file__).resolve().parents[4]
DIR_REF = RAIZ / "referencias" / "vegetacao"
DIR_SERIES = DIR_REF / "series"  # séries derivadas versionadas (demo offline), com FONTE.md
PRODUTOS = json.loads((DIR_REF / "produtos.json").read_text(encoding="utf-8"))
PARAMETROS = json.loads((DIR_REF / "parametros.json").read_text(encoding="utf-8"))
GRADE = PRODUTOS["grade_senoidal_modis"]
CASAS_ID = 6
# Limite técnico por anel lido do arquivo único de limites (D-009, #71); mesmo valor do CAR.
MAX_VERTICES = int(json.loads((RAIZ / "backend" / "src" / "tellus" / "contrato" / "limites.json")
                              .read_text(encoding="utf-8"))["vertices_por_anel_max"]["valor"])

MODIS = ("MOD13Q1", "MYD13Q1")
ORIGEM = {
    "MOD13Q1": "NASA LP DAAC MOD13Q1 v061 (MODIS/Terra)",
    "MYD13Q1": "NASA LP DAAC MYD13Q1 v061 (MODIS/Aqua)",
    "HLS": "NASA LP DAAC HLS v2.0 (HLSL30/HLSS30)",
}
AVISO_CONTEXTO = (
    "Contexto histórico de cobertura vegetal: mostra como a área esteve no passado. "
    "Não estima colheita e não indica o que vai acontecer na próxima safra."
)
DECISAO = PARAMETROS["decisao"]


def _dir_cache() -> Path:
    return Path(os.environ.get("TELLUS_CACHE_VEGETACAO", RAIZ / "data" / "raw" / "vegetacao"))


class ErroVegetacao(Exception):
    def __init__(self, codigo: str, mensagem: str, origem: str, status: int = 404, campo: str | None = None):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.origem, self.status, self.campo = codigo, mensagem, origem, status, campo


def _aviso(codigo: str, mensagem: str) -> dict:
    return {"codigo": codigo, "mensagem": mensagem}


# ---------------------------------------------------------------- área


def chave_ponto(lat: float, lon: float) -> str:
    return f"p_{lat:.6f}_{lon:.6f}".replace("-", "m").replace(".", "d")


def area_do_pedido(lat=None, lon=None, geometria: dict | None = None, id_geometria: str | None = None) -> dict:
    """Ponto (lat/lon) ou geometria confirmada (com o id_geometria conferido na spec 002)."""
    if geometria is not None:
        erros = regras_car.validar_poligono(geometria, MAX_VERTICES)
        if erros:
            raise ErroVegetacao("geometria_invalida", "Geometria inválida: " + "; ".join(erros), "pedido", 422, "geometria")
        can = regras_car.canonica(geometria, CASAS_ID)
        ident = regras_car.id_geometria(can, CASAS_ID)
        if id_geometria is None or id_geometria != ident:
            raise ErroVegetacao(
                "geometria_nao_confirmada",
                "A geometria precisa vir com o id_geometria da confirmação. Confirme a área antes de abrir o contexto.",
                "pedido", 422, "id_geometria",
            )
        c_lat, c_lon = regras_car.centroide_bbox(can)
        return {
            "tipo": "geometria", "chave": ident, "id_geometria": ident, "geometria": can,
            "centroide": {"lat": round(c_lat, 6), "lon": round(c_lon, 6)},
            "area_ha": round(regras_car.area_ha(can), 2),
        }
    if lat is None or lon is None:
        raise ErroVegetacao("parametro_ausente", "Informe lat e lon, ou a geometria confirmada.", "pedido", 422, "lat")
    la, lo = validar_coordenadas(lat, lon)
    return {
        "tipo": "ponto", "chave": chave_ponto(la, lo), "id_geometria": None,
        "geometria": {"type": "Point", "coordinates": [lo, la]},
        "centroide": {"lat": la, "lon": lo}, "area_ha": None,
    }


def _area_publica(area: dict, n_pixels: int, pesos: Mapping[str, float]) -> dict:
    return {
        "tipo": area["tipo"], "chave": area["chave"], "id_geometria": area["id_geometria"],
        "centroide": area["centroide"], "area_ha": area["area_ha"], "n_pixels": n_pixels,
        "pixels": [{"pixel": p, "peso": round(w, 4)} for p, w in sorted(pesos.items())],
    }


# ---------------------------------------------------------------- cache


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _ler_cache(dir_cache: Path, chave: str, produto: str, dir_series: Path | None = None) -> tuple[dict, list[dict], list[dict]] | None:
    """Cache local primeiro; sem ele, a série derivada versionada em referencias/vegetacao/series/."""
    tipo = "cache_local"
    pasta = dir_cache / chave
    p_csv, p_meta = pasta / f"{produto}.csv", pasta / f"{produto}.meta.json"
    if not (p_csv.exists() and p_meta.exists()) and dir_series is not None:
        pasta = dir_series / chave
        p_csv, p_meta = pasta / f"{produto}.csv", pasta / f"{produto}.meta.json"
        tipo = "referencia_versionada"
    if not p_csv.exists() or not p_meta.exists():
        return None
    meta = json.loads(p_meta.read_text(encoding="utf-8")) | {"_tipo": tipo}
    with p_csv.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    avisos = []
    if meta.get("sha256") and meta["sha256"] != _sha256(p_csv):
        avisos.append(_aviso("cache_alterado", f"O arquivo de cache de {ORIGEM[produto]} não confere com o hash registrado."))
    return meta, linhas, avisos


def _int(s: str | None) -> int | None:
    return None if s is None or s.strip() == "" else int(float(s))


# ---------------------------------------------------------------- proveniência


def _escala(produto_ref: dict) -> str:
    return (
        f"Valor de pixel de satélite ({produto_ref['resolucao']['espacial_texto']}) na área pedida; "
        "não é medição da lavoura nem da fazenda."
    )


def _status_regras(produto: str) -> dict:
    chave = "regra_qualidade_hls" if produto == "HLS" else "regra_qualidade_modis"
    itens = {"indice": "indice", "regra_qualidade": chave, "janela_meses": "janela_meses",
             "minimo_composicoes_validas": "minimo_composicoes_validas"}
    return {k: {"status": PARAMETROS[v]["status"], "decisao": DECISAO["id"], "issue": DECISAO["issue"]} for k, v in itens.items()}


def _prov(ref: dict, nome: str, periodo: dict, unidade: str, qualidade: dict, area_pub: dict, origem: dict) -> dict:
    return {
        "produto": nome,
        "versao": ref["versao"],
        "doi": ref["doi"],
        "periodo": periodo,
        "resolucao": ref["resolucao"],
        "unidade": unidade,
        "qualidade": qualidade,
        "area": {k: area_pub[k] for k in ("tipo", "chave", "id_geometria", "area_ha", "n_pixels")},
        "escala": _escala(ref),
        "limitacao": ref["limitacao"],
        "origem": origem,
        "status": _status_regras("HLS" if nome.startswith("HLS") else nome),
    }


# ---------------------------------------------------------------- indicadores


def _indicadores(ref, nome, obs: list[dict], datas_valores, unidade_indice, area_pub, origem, rotulo) -> list[dict]:
    """Agregações da série. Cada uma repete a proveniência completa (nada se perde ao agregar)."""
    if not obs:
        return []
    periodo = {"inicio": obs[0]["periodo"]["inicio"], "fim": obs[-1]["periodo"]["fim"]}
    n_val = sum(1 for o in obs if o["valor"] is not None)
    qual = {"n_validas": n_val, "n_total": len(obs), "regra": "lacunas contadas; nunca preenchidas"}
    d0, d1 = dt.date.fromisoformat(periodo["inicio"]), dt.date.fromisoformat(periodo["fim"])
    saida = [
        {"nome": f"{rotulo}_validas", "valor": n_val, "de": len(obs),
         **_prov(ref, nome, periodo, rotulo, qual, area_pub, origem)},
        {"nome": "meses_cobertos", "valor": round(((d1 - d0).days + 1) / (365.25 / 12), 1),
         **_prov(ref, nome, periodo, "meses", qual, area_pub, origem)},
    ]
    for m in regras.sazonalidade_mensal(datas_valores):
        qm = {"n_validas": m["n_validas"], "n_total": m["n_composicoes"],
              "regra": "média só das observações válidas do mês em todos os anos; lacunas não entram"}
        saida.append({
            "nome": "media_mensal", "mes": m["mes"], "valor": m["media"], "minimo": m["minimo"], "maximo": m["maximo"],
            **_prov(ref, nome, periodo, unidade_indice, qm, area_pub, origem),
        })
    return saida


def _janela(datas: list[str], inicio: str | None, fim: str | None) -> tuple[dt.date, dt.date] | None:
    """Sem inicio/fim: últimos `janela_meses` contados da última data do cache (determinístico)."""
    if not datas:
        return None
    if inicio is None and fim is None:
        ultima = dt.date.fromisoformat(datas[-1])
        corte = ultima - dt.timedelta(days=round(PARAMETROS["janela_meses"]["valor"] * 365.25 / 12))
        return corte + dt.timedelta(days=1), ultima
    ini = max(dt.date.fromisoformat(inicio), dt.date.fromisoformat(datas[0])) if inicio else dt.date.fromisoformat(datas[0])
    f = min(dt.date.fromisoformat(fim), dt.date.fromisoformat(datas[-1])) if fim else dt.date.fromisoformat(datas[-1])
    return (ini, f) if ini <= f else None


# ---------------------------------------------------------------- fontes


def _indisponivel(produto: str, codigo: str, mensagem: str) -> dict:
    return {
        "produto": produto, "estado": "indisponivel", "origem_nome": ORIGEM[produto],
        "motivo": {"codigo": codigo, "mensagem": mensagem}, "serie": [], "indicadores": [],
    }


def _origem(meta: dict, produto: str) -> dict:
    return {
        "nome": ORIGEM[produto], "tipo": meta.get("_tipo", "cache_local"), "obtido_em": meta.get("obtido_em"),
        "consulta": meta.get("consulta"), "sha256": meta.get("sha256"), "sintetico": bool(meta.get("sintetico")),
    }


def _suficiencia(serie: list[dict]) -> dict:
    n = sum(1 for o in serie if o["valor"] is not None)
    minimo = PARAMETROS["minimo_composicoes_validas"]
    estado = "suficiente" if n >= minimo["valor"] else "insuficiente"
    msg = (f"{n} observações válidas na janela; mínimo provisório {minimo['valor']} ({minimo['status']}, "
           f"issue {DECISAO['issue']}).")
    if estado == "insuficiente":
        msg += " Série insuficiente para descrever a sazonalidade; as lacunas não foram preenchidas."
    return {"estado": estado, "n_validas": n, "minimo": minimo["valor"], "status": minimo["status"], "mensagem": msg}


def fonte_modis(produto: str, area: dict, indice: str, inicio, fim, dir_cache: Path, dir_series: Path | None = None) -> dict:
    ref = PRODUTOS[produto]
    lido = _ler_cache(dir_cache, area["chave"], produto, dir_series)
    if lido is None:
        return _indisponivel(
            produto, "sem_cache",
            f"Não há série de {ORIGEM[produto]} guardada para esta área. "
            "Rode scripts/preparar_vegetacao.py com internet.",
        )
    meta, linhas, avisos = lido
    pesos = {p: float(w) for p, w in meta["pesos"].items()}
    area_pub = _area_publica(area, len(pesos), pesos)
    origem = _origem(meta, produto)
    meta_ind = ref["indices"][indice]
    regra = PARAMETROS["regra_qualidade_modis"]["valor"]
    cob_min = PARAMETROS["cobertura_minima_area"]["valor"]
    por_data: dict[str, dict[str, tuple[float | None, str | None]]] = {}
    for l in linhas:
        por_data.setdefault(l["data"], {})[l["pixel"]] = regras.valor_modis(
            _int(l.get(indice)), _int(l.get("pixel_reliability")), meta_ind, regra, _int(l.get("vi_quality"))
        )
    jan = _janela(sorted(por_data), inicio, fim)
    cal = ref["calendario"]
    datas = regras.calendario(*jan, cal["dia_juliano_inicial"], cal["passo_dias"]) if jan else []
    serie, dv = [], []
    for d in datas:
        ag = regras.agregar_area(por_data.get(d.isoformat(), {}), pesos, cob_min)
        periodo = {"inicio": d.isoformat(), "fim": regras.fim_composicao(d, cal["passo_dias"]).isoformat()}
        qual = {"estado": "valida" if ag["valor"] is not None else "lacuna", "motivo": ag["motivo"],
                "cobertura_valida": ag["cobertura_valida"], "fracao_por_motivo": ag["fracao_por_motivo"]}
        serie.append({"data": d.isoformat(), "indice": indice, "valor": ag["valor"],
                      **_prov(ref, produto, periodo, meta_ind["unidade"], qual, area_pub, origem)})
        dv.append((d, ag["valor"]))
    return {
        "produto": produto, "estado": "disponivel", "origem_nome": ORIGEM[produto], "origem": origem,
        "area": area_pub, "indice": indice, "serie": serie, "suficiencia": _suficiencia(serie),
        "indicadores": _indicadores(ref, produto, serie, dv, meta_ind["unidade"], area_pub, origem, "composicoes"),
        "avisos": avisos,
    }


def fonte_hls(area: dict, indice: str, inicio, fim, dir_cache: Path, ambiente: Mapping[str, str],
              dir_series: Path | None = None) -> dict:
    ref = PRODUTOS["HLS"]
    lido = _ler_cache(dir_cache, area["chave"], "HLS", dir_series)
    if lido is None:
        if not ambiente.get("EARTHDATA_TOKEN"):
            return _indisponivel(
                "HLS", "sem_credencial",
                "O HLS exige conta NASA Earthdata e não há credencial configurada (EARTHDATA_TOKEN). "
                "O contexto segue só com MODIS.",
            )
        return _indisponivel(
            "HLS", "sem_cache",
            f"Não há série de {ORIGEM['HLS']} guardada para esta área. O contexto segue só com MODIS.",
        )
    meta, linhas, avisos = lido
    pesos = {p: float(w) for p, w in meta["pesos"].items()}
    area_pub = _area_publica(area, len(pesos), pesos)
    origem = _origem(meta, "HLS")
    regra = PARAMETROS["regra_qualidade_hls"]["valor"]
    cob_min = PARAMETROS["cobertura_minima_area"]["valor"]
    unidade = ref["indices"][indice]["unidade"]
    por_cena: dict[tuple[str, str], dict[str, tuple[float | None, str | None]]] = {}
    for l in linhas:
        bandas = {b: _int(l.get(b)) for b in ("azul", "vermelho", "nir")}
        por_cena.setdefault((l["data"], l["sensor"]), {})[l["pixel"]] = regras.valor_hls(
            bandas, _int(l.get("fmask")), indice, ref["bandas"], regra
        )
    jan = _janela(sorted(d for d, _ in por_cena), inicio, fim)
    serie, dv = [], []
    for (d, sensor) in sorted(por_cena):
        if jan is None or not jan[0].isoformat() <= d <= jan[1].isoformat():
            continue
        ag = regras.agregar_area(por_cena[(d, sensor)], pesos, cob_min)
        qual = {"estado": "valida" if ag["valor"] is not None else "lacuna", "motivo": ag["motivo"],
                "cobertura_valida": ag["cobertura_valida"], "fracao_por_motivo": ag["fracao_por_motivo"]}
        serie.append({"data": d, "sensor": sensor, "indice": indice, "valor": ag["valor"],
                      **_prov(ref, f"HLS{sensor}", {"inicio": d, "fim": d}, unidade, qual, area_pub, origem)})
        dv.append((dt.date.fromisoformat(d), ag["valor"]))
    return {
        "produto": "HLS", "estado": "disponivel", "origem_nome": ORIGEM["HLS"], "origem": origem,
        "area": area_pub, "indice": indice, "serie": serie, "suficiencia": _suficiencia(serie),
        "indicadores": _indicadores(ref, "HLS", serie, dv, unidade, area_pub, origem, "cenas"),
        "avisos": avisos,
    }


# ---------------------------------------------------------------- resposta


def _data_ok(nome: str, valor: str | None) -> str | None:
    if valor is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        raise ErroVegetacao("parametro_invalido", f"Data inválida em {nome}: use AAAA-MM-DD.", "pedido", 422, nome)
    try:
        dt.date.fromisoformat(valor)
    except ValueError:
        raise ErroVegetacao("parametro_invalido", f"Data inválida em {nome}: use AAAA-MM-DD.", "pedido", 422, nome) from None
    return valor


def contexto(
    lat=None, lon=None, geometria: dict | None = None, id_geometria: str | None = None,
    indice: str | None = None, inicio: str | None = None, fim: str | None = None,
    dir_cache: Path | None = None, ambiente: Mapping[str, str] | None = None,
    produtos: list[str] | None = None, dir_series: Path | None = DIR_SERIES,
) -> dict:
    dir_cache = dir_cache or _dir_cache()
    produtos = produtos or PARAMETROS["produtos_modis"]["valor"]
    if any(p not in PARAMETROS["produtos_modis"]["opcoes"] for p in produtos):
        raise ErroVegetacao("parametro_invalido", "Produto MODIS não suportado.", "pedido", 422, "produtos")
    ambiente = os.environ if ambiente is None else ambiente
    indice = indice or PARAMETROS["indice"]["valor"]
    if indice not in PARAMETROS["indice"]["opcoes"]:
        raise ErroVegetacao("parametro_invalido", f"Índice não suportado: {indice}. Use ndvi ou evi.", "pedido", 422, "indice")
    inicio, fim = _data_ok("inicio", inicio), _data_ok("fim", fim)
    area = area_do_pedido(lat, lon, geometria, id_geometria)
    fontes = [fonte_modis(p, area, indice, inicio, fim, dir_cache, dir_series) for p in produtos]
    fontes.append(fonte_hls(area, indice, inicio, fim, dir_cache, ambiente, dir_series))
    if all(f["estado"] == "indisponivel" for f in fontes):
        raise ErroVegetacao(
            "sem_cache",
            "Não há série de vegetação guardada para esta área. Rode scripts/preparar_vegetacao.py com internet. "
            "A falta deste contexto não bloqueia o restante da análise.",
            ", ".join(ORIGEM[p] for p in (*produtos, "HLS")),
        )
    avisos = [
        _aviso("contexto_historico", AVISO_CONTEXTO),
        _aviso("escala", "MODIS tem pixel de 250 m e HLS de 30 m: os valores descrevem a vizinhança, não a lavoura."),
        _aviso(
            "decisao_pendente",
            f"Produto, índice, janela de {PARAMETROS['janela_meses']['valor']} meses, mínimo de "
            f"{PARAMETROS['minimo_composicoes_validas']['valor']} composições válidas e regra de qualidade são hipótese "
            f"operacional do protótipo ({DECISAO['id']}, issue {DECISAO['issue']}), não parâmetro validado. Veja 'parametros'.",
        ),
    ]
    for f in fontes:
        if f["estado"] == "indisponivel":
            avisos.append(_aviso(f"{f['produto'].lower()}_indisponivel", f["motivo"]["mensagem"]))
        else:
            o = f["origem"]
            onde = "cache local" if o["tipo"] == "cache_local" else "série versionada do repositório"
            avisos.append(_aviso("cache", f"{o['nome']}: dados de {onde} obtidos em {o['obtido_em']}."))
            if f["suficiencia"]["estado"] == "insuficiente":
                avisos.append(_aviso(f"{f['produto'].lower()}_insuficiente", f"{o['nome']}: {f['suficiencia']['mensagem']}"))
            if o["sintetico"]:
                avisos.append(_aviso("dado_sintetico", f"{o['nome']}: série SINTÉTICA de teste, não é dado real."))
            avisos.extend(f.pop("avisos"))
    return {
        "finalidade": "contexto_historico",
        "area": {k: area[k] for k in ("tipo", "chave", "id_geometria", "centroide", "area_ha")},
        "indice": indice,
        "periodo_pedido": {"inicio": inicio, "fim": fim},
        "parametros": {
            "decisao": DECISAO,
            **{k: PARAMETROS[k] for k in ("produtos_modis", "indice", "janela_meses", "minimo_composicoes_validas",
                                           "regra_qualidade_modis", "regra_qualidade_hls", "cobertura_minima_area")},
        },
        "fontes": fontes,
        "avisos": avisos,
    }
