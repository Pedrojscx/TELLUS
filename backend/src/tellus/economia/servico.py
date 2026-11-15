"""Margem por hectare em três cenários, com custo Conab rastreável, preço CEPEA e premissas editáveis (spec 007)."""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tellus.localizacao.regras import haversine_km

from . import conab

RAIZ = Path(__file__).resolve().parents[4]
REF = RAIZ / "referencias" / "economia"
CULTURA_CONAB = {"milho_2a_safra": "milho_2a_safra", "sorgo_granifero_2a_safra": "sorgo", "braquiaria_cobertura": None}
NIVEL_PADRAO = "custo_operacional"
# D-006 (hipótese visível): conservador = perda no percentil 75; central = 50; favorável = 25
PERCENTIS_PADRAO = {"conservador": "75", "central": "50", "favoravel": "25"}
DESCRICAO_PERCENTIS = ("Cenários pela perda relativa simulada (006): conservador = percentil 75 da perda "
                       "(3 em cada 4 anos perderam menos), central = mediana, favorável = percentil 25. Hipótese D-006, editável.")


class ErroEconomia(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


@lru_cache(maxsize=8)
def _conab(cultura_conab: str) -> dict:
    return json.loads((REF / f"conab_{cultura_conab}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _cepea_milho() -> dict:
    return json.loads((REF / "cepea_milho.json").read_text(encoding="utf-8"))


def praca_mais_proxima(lat: float, lon: float, cultura: str) -> dict | None:
    """FR-001: a praça mais próxima entre as que têm planilha da MESMA cultura; ano mais recente da praça."""
    cc = CULTURA_CONAB.get(cultura)
    if cc is None:
        return None
    dados = _conab(cc)
    por_praca: dict[str, dict] = {}
    for p in dados["planilhas"]:
        atual = por_praca.get(p["codigo_ibge"])
        if atual is None or (p["ano"], not p["ogm"]) > (atual["ano"], not atual["ogm"]):
            por_praca[p["codigo_ibge"]] = p
    melhor = min(por_praca.values(), key=lambda p: (round(haversine_km(lat, lon, p["lat"], p["lon"]), 6), p["codigo_ibge"]))
    return melhor | {"distancia_km": round(haversine_km(lat, lon, melhor["lat"], melhor["lon"]), 1),
                     "fonte_arquivo": {k: dados[k] for k in ("fonte", "arquivo", "url", "obtido_em", "sha256")}}


def _preco_padrao(cultura: str) -> dict:
    if cultura == "milho_2a_safra":
        c = _cepea_milho()
        ultimo = c["serie"][-1]
        return {"id": "preco_r_saca", "nome": "Preço de venda", "valor": ultimo["r_saca"], "unidade": "R$/saca de 60 kg",
                "status": "fonte", "fonte": {"fonte": c["fonte"], "indicador": c["indicador"], "praca": c["praca"],
                                             "data": ultimo["data"], "url": c["url"], "obtido_em": c["obtido_em"]},
                "nota": "Preço à vista na região de Campinas-SP; não desconta o frete até a fazenda (o transporte externo já é item de custo da Conab)."}
    if cultura == "sorgo_granifero_2a_safra":
        return {"id": "preco_r_saca", "nome": "Preço de venda", "valor": None, "unidade": "R$/saca de 60 kg", "status": "indisponivel",
                "motivo": "D-005: o CEPEA não publica indicador de sorgo e o portal de preços da Conab não oferece conexão segura "
                          "(certificado inválido). Informe o preço negociado para ver a margem."}
    return {"id": "preco_r_saca", "nome": "Preço de venda", "valor": 0.0, "unidade": "R$/saca de 60 kg", "status": "nao_se_aplica",
            "motivo": "A planta de cobertura não é comercializada; a receita é zero."}


def _hash(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def _premissas(lat: float, lon: float, cultura: str) -> dict:
    praca = praca_mais_proxima(lat, lon, cultura)
    if praca:
        prod = {"id": "produtividade_kg_ha", "nome": "Produtividade de referência (sem estresse hídrico)", "valor": praca["produtividade_kg_ha"],
                "unidade": "kg/ha", "status": "fonte", "fonte": {"fonte": "Conab", "planilha": praca["aba"], "tipo": praca["tipo_produtividade"]}}
    else:
        prod = {"id": "produtividade_kg_ha", "nome": "Produtividade de referência", "valor": 0.0, "unidade": "kg/ha",
                "status": "nao_se_aplica", "motivo": "Cobertura sem produção de grão."}
    return {"praca": praca, "preco": _preco_padrao(cultura), "produtividade": prod}


def _cenarios(perda_quantis: dict | None, prod: float | None, preco: float | None, custo: float | None, percentis: dict) -> dict:
    out = {}
    for nome, q in percentis.items():
        perda = 0.0 if perda_quantis is None else perda_quantis.get(q)
        prod_c = None if prod is None or perda is None else round(prod * (1 - perda), 1)
        receita = None if prod_c is None or preco is None else round(prod_c / 60 * preco, 2)
        margem = None if receita is None or custo is None else round(receita - custo, 2)
        out[nome] = {"percentil_perda": int(q), "perda_relativa": perda, "produtividade_kg_ha": prod_c,
                     "sacas_ha": None if prod_c is None else round(prod_c / 60, 2), "receita_r_ha": receita,
                     "custo_r_ha": custo, "margem_r_ha": margem}
    return out


def margem(lat: float, lon: float, cultura: str, perda_quantis: dict | None, edicoes: dict | None = None,
           percentis: dict | None = None, informacoes: dict | None = None) -> dict:
    """`informacoes`: {chave da edição: {"origem_informada": str, "data_informada": "AAAA-MM-DD"}} (contrato 1.1.0).
    Registra de onde o produtor tirou o valor (ex.: cotação do sorgo, que não tem indicador oficial — D-005)."""
    if cultura not in CULTURA_CONAB:
        raise ErroEconomia("cultura_invalida", f"Cultura deve ser uma de {sorted(CULTURA_CONAB)}.", "cultura")
    percentis = percentis or PERCENTIS_PADRAO
    if set(percentis) != set(PERCENTIS_PADRAO) or any(str(v) not in {"10", "25", "50", "75", "90"} for v in percentis.values()):
        raise ErroEconomia("percentis_invalidos", "Percentis devem ser conservador/central/favoravel com 10, 25, 50, 75 ou 90.", "percentis")
    percentis = {k: str(v) for k, v in percentis.items()}
    ed = dict(edicoes or {})
    base = _premissas(lat, lon, cultura)
    praca = base["praca"]
    nivel = ed.pop("nivel_custo", NIVEL_PADRAO)
    if nivel not in conab.NIVEIS:
        raise ErroEconomia("nivel_invalido", f"nivel_custo deve ser um de {list(conab.NIVEIS)}.", "nivel_custo")
    ajustes_itens = {k.split(".", 1)[1]: v for k, v in ed.items() if k.startswith("custo_item.")}
    for k, v in ajustes_itens.items():
        if not isinstance(v, (int, float)) or v < 0:
            raise ErroEconomia("fora_do_dominio", f"custo_item.{k} deve ser um valor ≥ 0 em R$/ha.", f"custo_item.{k}")
        if praca and k not in {i["codigo"] for i in praca["itens"]}:
            raise ErroEconomia("item_desconhecido", f"Item {k} não existe na planilha {praca['aba']}.", f"custo_item.{k}")
    alteracoes = []

    def editar(chave, padrao, lo, hi, unidade):
        if chave not in ed:
            return padrao, False
        v = ed[chave]
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
            raise ErroEconomia("fora_do_dominio", f"{chave} = {v} fora do domínio aceito ({lo} a {hi} {unidade}).", chave)
        alt = {"premissa": chave, "valor_anterior": padrao, "valor_novo": v, "unidade": unidade, "origem_novo": "produtor"}
        info = (informacoes or {}).get(chave)
        if info:
            alt |= {"origem_informada": info["origem_informada"], "data_informada": info["data_informada"]}
        alteracoes.append(alt)
        return v, True

    preco_pad = base["preco"]["valor"]
    preco, preco_ed = editar("preco_r_saca", preco_pad, 0, 1000, "R$/saca de 60 kg")
    prod_pad = base["produtividade"]["valor"]
    prod, prod_ed = editar("produtividade_kg_ha", prod_pad, 0, 30000, "kg/ha")
    itens, custo_pad, custo_itens = [], None, None
    if praca:
        custo_pad, _ = conab.custo_do_nivel(praca, nivel)
        custo_itens, itens = conab.custo_do_nivel(praca, nivel, ajustes_itens)
        for k, v in ajustes_itens.items():
            antes = next(i["valor_r_ha"] for i in praca["itens"] if i["codigo"] == k)
            alt = {"premissa": f"custo_item.{k}", "valor_anterior": antes, "valor_novo": v, "unidade": "R$/ha", "origem_novo": "produtor"}
            info = (informacoes or {}).get(f"custo_item.{k}")
            if info:
                alt |= {"origem_informada": info["origem_informada"], "data_informada": info["data_informada"]}
            alteracoes.append(alt)
    custo, custo_ed = editar("custo_r_ha", custo_itens, 0, 100000, "R$/ha")
    if "nivel_custo" in (edicoes or {}):
        alteracoes.append({"premissa": "nivel_custo", "valor_anterior": NIVEL_PADRAO, "valor_novo": nivel, "unidade": "—", "origem_novo": "produtor"})
    cenarios = _cenarios(perda_quantis, prod, preco, custo, percentis)
    faltas = []
    if preco is None:
        faltas.append(base["preco"].get("motivo", "preço indisponível"))
    if custo is None:
        faltas.append("Sem planilha de custo da Conab para esta cultura (cobertura). Informe o custo em R$/ha (custo_r_ha).")
    if perda_quantis is None and cultura != "braquiaria_cobertura":
        faltas.append("Sem simulação hídrica (006) para os cenários de produtividade.")
    disponivel = not faltas
    estado = "fonte"
    if preco_ed or prod_ed or custo_ed or ajustes_itens or "nivel_custo" in (edicoes or {}):
        estado = "com_premissas_do_produtor"
    comparacao = None
    if alteracoes and disponivel:
        custo_ref = custo_pad
        anterior = _cenarios(perda_quantis, prod_pad, preco_pad, custo_ref, percentis) if None not in (preco_pad, custo_ref) else None
        comparacao = {"margem_anterior_r_ha": None if anterior is None else {k: v["margem_r_ha"] for k, v in anterior.items()},
                      "margem_nova_r_ha": {k: v["margem_r_ha"] for k, v in cenarios.items()}}
    preco_premissa = base["preco"] | {"valor_usado": preco, "editado": preco_ed}
    info_preco = (informacoes or {}).get("preco_r_saca") if preco_ed else None
    if info_preco:
        preco_premissa["informado"] = {"origem_informada": info_preco["origem_informada"],
                                       "data_informada": info_preco["data_informada"]}
    if preco_ed and base["preco"]["status"] == "indisponivel":
        preco_premissa["status"] = "informado_pelo_produtor"
    premissas = {
        "preco": preco_premissa,
        "produtividade": base["produtividade"] | {"valor_usado": prod, "editado": prod_ed},
        "custo": {"nivel": nivel, "valor_padrao_r_ha": custo_pad, "valor_usado_r_ha": custo, "editado": custo_ed or bool(ajustes_itens),
                  "status": "fonte" if praca else "indisponivel", "unidade": "R$/ha"},
        "percentis": {"valores": percentis, "status": "hipotese", "descricao": DESCRICAO_PERCENTIS},
    }
    custo_conab = None
    if praca:
        custo_conab = {"praca": f"{praca['praca']}-{praca['uf']}", "codigo_ibge": praca["codigo_ibge"], "distancia_km": praca["distancia_km"],
                       "planilha": praca["aba"], "mes_referencia": praca["mes_referencia"], "sistema": praca["sistema"],
                       "unidade": "R$/ha", "nivel": nivel, "itens": itens, "total_nivel_r_ha": custo_itens,
                       "totais_planilha": praca["totais"], "avisos_planilha": praca["avisos"], "fonte": praca["fonte_arquivo"]}
    return {
        "cultura": cultura,
        "margem_disponivel": disponivel,
        "motivos_indisponivel": faltas,
        "estado": estado,
        "cenarios": cenarios if disponivel else {k: v | {"margem_r_ha": None} for k, v in cenarios.items()},
        "custo_conab": custo_conab,
        "premissas": premissas,
        "alteracoes": alteracoes,
        "comparacao": comparacao,
        "versao_premissas": _hash({"premissas": premissas, "itens": itens, "perda": perda_quantis}),
        "formula": "margem = produtividade de referência × (1 − perda do cenário) ÷ 60 × preço − custo do nível (R$/ha)",
    }
