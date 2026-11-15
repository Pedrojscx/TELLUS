"""Calendário ZARC por município, cultura, grupo e solo, com proveniência (spec 004)."""

from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
from pathlib import Path

from . import regras

RAIZ = Path(__file__).resolve().parents[4]
DIR_REF = RAIZ / "referencias" / "zarc"
CULTURAS = json.loads((DIR_REF / "culturas.json").read_text(encoding="utf-8"))
SAFRA = CULTURAS["safra_vigente"]
ROTULO_SOLO = {
    "1": "Tipo 1 (arenoso)", "2": "Tipo 2 (textura média)", "3": "Tipo 3 (argiloso)",
    **{f"AD{i}": f"AD{i} (classe de água disponível {i})" for i in range(1, 7)},
}
SIGNIFICADO = (
    "Risco ZARC = probabilidade oficial de perda de produtividade (20, 30 ou 40%) definida pela portaria do MAPA "
    "para o decêndio de semeadura. Não é o risco histórico de falta de água calculado pelo TELLUS."
)


class ErroZarc(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 404):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


@lru_cache(maxsize=32)
def _uf(safra: str, uf: str) -> dict | None:
    p = DIR_REF / safra.replace(" / ", "-") / f"{uf}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _uf_do_ibge(codigo_ibge: str) -> str:
    from tellus.localizacao.referencias import carregar

    m = carregar().municipios.get(codigo_ibge)
    if not m:
        raise ErroZarc("municipio_nao_encontrado", f"Município {codigo_ibge} não existe na lista do IBGE.", "codigo_ibge")
    return m["uf"]


def _data_iso(br: str) -> str:
    d, m, a = br.split("/")
    return f"{a}-{m}-{d}"


def calendario(codigo_ibge: str, cultura: str, grupo: str | None = None, solo: str | None = None) -> dict:
    """Janela por grupo e solo. Grupo None ("não sei") devolve todos os grupos separados."""
    if cultura not in CULTURAS["culturas"]:
        raise ErroZarc("cultura_invalida", f"Cultura desconhecida: {cultura}. Use uma de {sorted(CULTURAS['culturas'])}.", "cultura", 422)
    uf = _uf_do_ibge(codigo_ibge)
    dados = _uf(SAFRA, uf)
    base = {"codigo_ibge": codigo_ibge, "uf": uf, "cultura": cultura, "safra": SAFRA,
            "manejo": CULTURAS["manejo"], "significado": SIGNIFICADO}
    if dados is None:
        return base | {"disponivel": False, "motivo": f"O ZARC de {uf} ainda não foi baixado neste ambiente "
                                                      f"(rode scripts/preparar_zarc.py {uf}).", "grupos": []}
    por_cultura = dados["municipios"].get(codigo_ibge, {}).get(cultura)
    if not por_cultura:
        return base | {"disponivel": False, "grupos": [],
                       "motivo": "Sem ZARC publicado para esta cultura neste município na safra vigente. "
                                 "Nenhuma janela foi inferida de município vizinho."}
    conjuntos = {(c["cultura"], c["grupo"]): c for c in dados["conjuntos"]}
    grupos_sel = [grupo] if grupo else sorted(por_cultura)
    saida = []
    for g in grupos_sel:
        solos = por_cultura.get(g)
        if solos is None:
            saida.append({"grupo": g, "disponivel": False, "motivo": "Grupo sem ZARC neste município."})
            continue
        conj = conjuntos[(cultura, g)]
        proveniencia = {
            "fonte": "MAPA — Zoneamento Agrícola de Risco Climático (SISZARC, relatório de publicações)",
            "portaria": conj["portaria"],
            "data_portaria": _data_iso(conj["data_portaria"]),
            "safra": conj["safra"],
            "vigente": conj["safra"] == SAFRA,
            "obtido_em": conj["obtido_em"],
            "url": CULTURAS["url"],
            "arquivo_sha256": conj["sha256"],
        }
        lista_solos = []
        for s, v in sorted(solos.items()):
            if solo and s != solo:
                continue
            riscos = regras.decodificar(v["riscos"])
            lista_solos.append({"solo": s, "rotulo_solo": ROTULO_SOLO.get(s, s), "janela": regras.janela(riscos)})
        saida.append({"grupo": g, "disponivel": True, "solos": lista_solos, "proveniencia": proveniencia})
    return base | {"disponivel": True, "grupo_informado": grupo, "grupos": saida}


def consultar_data(codigo_ibge: str, cultura: str, data: str, grupo: str | None = None, solo: str | None = None) -> dict:
    try:
        d = dt.date.fromisoformat(data)
    except ValueError:
        raise ErroZarc("data_invalida", "Data no formato AAAA-MM-DD.", "data", 422)
    cal = calendario(codigo_ibge, cultura, grupo, solo)
    if not cal["disponivel"]:
        return cal | {"data": data, "resultados": []}
    resultados = []
    for g in cal["grupos"]:
        if not g["disponivel"]:
            continue
        for s in g["solos"]:
            janela = {j["decendio"]: j["risco_zarc_pct"] for j in s["janela"]}
            dec = regras.decendio(d)
            resultados.append({
                "grupo": g["grupo"], "solo": s["solo"], "rotulo_solo": s["rotulo_solo"], "decendio": dec,
                "dentro_da_janela": dec in janela, "risco_zarc_pct": janela.get(dec),
                "portaria": g["proveniencia"]["portaria"],
            })
    return {k: v for k, v in cal.items() if k != "grupos"} | {"data": data, "resultados": resultados}


def permitido(codigo_ibge: str, cultura: str, data: str, grupo: str, solo: str) -> bool:
    """Bloqueio usado pela recomendação (FR-004): só True com risco oficial diferente de zero."""
    r = consultar_data(codigo_ibge, cultura, data, grupo, solo)
    return any(x["dentro_da_janela"] for x in r.get("resultados", []))
