"""Adaptadores das saídas REAIS dos módulos para as seções do contrato e a montagem da resposta.

- risco_hidrico ← `tellus.motor.servico.simular` (spec 006)
- economia      ← `tellus.economia.servico.margem` (spec 007)
- recomendacao  ← spec 008 inexistente: seção `pendente`, sem conteúdo nem campos inventados
- contextos     ← respostas opacas da 009/010 (ou erro), isoladas do resultado principal

Os adaptadores só leem campos que os módulos já devolvem. Se um campo faltar, a proveniência
fica incompleta e o teste de cobertura acusa (nada é preenchido por suposição).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from . import regras, versao
from .modelos import CULTURAS
from .versao import VERSAO

AVISO_008 = ("A recomendação (spec 008, #48) ainda não existe. Esta resposta traz risco hídrico e margem por cultura, "
             "mas não ordena nem recomenda alternativas.")


def _s(v: Any) -> str:
    """Texto determinístico para um metadado estruturado (dict/list) do módulo de origem."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False, sort_keys=True)


def _periodo(p: Any) -> str:
    if isinstance(p, Mapping) and "inicio" in p and "fim" in p:
        return f"{p['inicio']} a {p['fim']}"
    return _s(p)


def _aviso(codigo: str, mensagem: str, origem: str) -> dict:
    return {"tipo": "aviso", "codigo": codigo, "mensagem": mensagem, "origem": origem}


def erro_fonte(exc: Exception, origem_padrao: str, cache_obtido_em: str | None = None, acao: str | None = None) -> dict:
    """Exceção de módulo (ErroClima/ErroMotor/ErroEconomia/...) → ErroFonte do contrato."""
    return {
        "tipo": "erro",
        "codigo": getattr(exc, "codigo", type(exc).__name__),
        "mensagem": getattr(exc, "mensagem", str(exc)),
        "origem": getattr(exc, "origem", None) or origem_padrao,
        "campo": getattr(exc, "campo", None),
        "cache": {"disponivel": cache_obtido_em is not None, "obtido_em": cache_obtido_em},
        "acao": acao,
    }


# ---------------------------------------------------------------- 006


def _prov_clima(chave: str, prov: Mapping, origem_dados: str, cobre: list[str]) -> dict:
    return {
        "id": chave, "fonte": _s(prov.get("fonte")), "versao": _s(prov.get("versao")), "periodo": _periodo(prov.get("periodo")),
        "unidade": _s(prov.get("unidade")), "localizacao": _s(prov.get("localizacao")),
        "qualidade": _s(prov.get("qualidade")) + (f"; resolução {prov['resolucao']}" if prov.get("resolucao") else ""),
        "situacao": "fonte" if origem_dados == "fonte" else "cache", "url": prov.get("url"), "obtido_em": prov.get("obtido_em"),
        "cobre": cobre,
    }


def secao_risco_hidrico(s: Mapping) -> tuple[dict, list[dict], list[str]]:
    """Seção 006 + estados de fonte + hipóteses declaradas pelo motor."""
    ent = s["entradas"]
    clima = ent["clima"]
    chuva, power = clima["proveniencia"]["chuva"], clima["proveniencia"]["power"]
    r = s["resultado"]
    z = ent["zarc"]
    ped = s["pedido"]
    provs = [
        {"id": "pedido", "fonte": "Pedido do produtor normalizado pelo motor (spec 006)", "versao": s["versao_entradas"],
         "periodo": f"colheita {ped['data_colheita_soja']}, plantio {ped['data_plantio']} (mês-dia, aplicado a cada ano)",
         "unidade": "graus decimais", "localizacao": f"{ped['lat']}, {ped['lon']} (município {ped['codigo_ibge']})",
         "qualidade": "informado e confirmado pelo produtor", "situacao": "pedido", "cobre": ["pedido.*"]},
        _prov_clima("imerg", chuva, clima["origem_dados"], ["por_ano.*.chuva_mm"]),
        _prov_clima("power", power, clima["origem_dados"], ["por_ano.*.etc_mm"]),
        {"id": "motor", "fonte": "TELLUS motor hídrico (spec 006): balanço FAO-56 cap. 8 e perda FAO-33 por fase; "
                                 "ETo FAO-56 Penman-Monteith com POWER; chuva IMERG",
         "versao": s["versao_entradas"], "periodo": _periodo(chuva.get("periodo")),
         "unidade": "mm; fração 0–1 (perda, ISNA, risco); ano", "localizacao": _s(chuva.get("localizacao")),
         "qualidade": f"{r['anos_validos']} anos válidos, {len(s['anos_excluidos'])} excluídos; frequência histórica, não previsão",
         "situacao": "calculado", "cobre": ["resultado.*", "por_ano.*", "anos_excluidos.*"]},
        {"id": "zarc", "fonte": f"ZARC/MAPA, portaria {z.get('portaria')}", "versao": f"portaria {z.get('portaria')}",
         "periodo": f"safra {z.get('safra')}, decêndio {z.get('decendio')}", "unidade": "% (risco oficial)",
         "localizacao": f"município {ped['codigo_ibge']}, solo {z.get('solo')}, {z.get('grupo')}",
         "qualidade": "risco oficial da portaria (medida distinta do risco histórico)", "situacao": "fonte",
         "cobre": ["resultado.risco_zarc_pct"]},
    ]
    secao = {
        "id": "risco_hidrico", "spec": "006 (#44)", "obrigatoria": True, "estado": "disponivel",
        "versao_modulo": s["versao_entradas"],
        "conteudo": {"pedido": s["pedido"], "resultado": r, "por_ano": s["por_ano"], "anos_excluidos": s["anos_excluidos"],
                     "premissa_chuva": s.get("premissa_chuva")},
        "proveniencia": provs,
        "avisos": [_aviso(a["codigo"], a["mensagem"], "spec 006") for a in s.get("avisos", [])],
        "erro": None,
    }
    estado = "ok" if clima["origem_dados"] == "fonte" else "cache"
    fontes = [{"fonte": _s(chuva.get("fonte")), "estado": estado, "obtido_em": chuva.get("obtido_em"), "secao": "risco_hidrico"},
              {"fonte": _s(power.get("fonte")), "estado": estado, "obtido_em": power.get("obtido_em"), "secao": "risco_hidrico"}]
    hipoteses = [a["mensagem"] for a in s.get("avisos", []) if a["codigo"] == "hipoteses"]
    return secao, fontes, hipoteses


# ---------------------------------------------------------------- 007


def secao_economia(r: Mapping, s: Mapping | None, cotacao: Mapping | None = None) -> dict:
    """Seção 007. `s` é a saída da 006 que deu a perda relativa (ou None).

    `cotacao` (1.1.0): a premissa de preço do PEDIDO com origem/data informadas. Se a 007 não repassar esses campos,
    a proveniência do preço é montada a partir do próprio pedido, sem inventar nada."""
    pr = r["premissas"]
    cc = r.get("custo_conab")
    provs = []
    local_praca = f"praça Conab {cc['praca']} a {cc['distancia_km']} km do ponto" if cc else ""
    if cc:
        f = cc["fonte"]
        provs.append({"id": "conab_custo", "fonte": f"{f['fonte']} — planilha {cc['planilha']}", "versao": f"{f['arquivo']} sha256 {f['sha256'][:12]}",
                      "periodo": cc["mes_referencia"], "unidade": cc["unidade"], "localizacao": local_praca,
                      "qualidade": f"estimativa ex-ante da Conab, {cc['sistema']}, nível {cc['nivel']}",
                      "situacao": "fonte", "url": f.get("url"), "obtido_em": f.get("obtido_em"),
                      "cobre": ["custo_conab.*", "premissas.custo.*", "cenarios.*.custo_r_ha"]})
    prod = pr["produtividade"]
    if prod.get("status") == "fonte" and cc:
        provs.append({"id": "conab_produtividade", "fonte": f"{prod['fonte']['fonte']} — planilha {prod['fonte']['planilha']}",
                      "versao": f"{cc['fonte']['arquivo']} sha256 {cc['fonte']['sha256'][:12]}", "periodo": cc["mes_referencia"],
                      "unidade": prod["unidade"], "localizacao": local_praca, "qualidade": prod["fonte"]["tipo"],
                      "situacao": "fonte", "url": cc["fonte"].get("url"), "obtido_em": cc["fonte"].get("obtido_em"),
                      "cobre": ["premissas.produtividade.*"]})
    elif prod.get("status") == "nao_se_aplica":
        provs.append({"id": "produtividade_nao_se_aplica", "fonte": "TELLUS economia (spec 007)", "versao": r["versao_premissas"],
                      "periodo": "não se aplica", "unidade": prod["unidade"], "localizacao": "não se aplica",
                      "qualidade": prod.get("motivo") or "não se aplica", "situacao": "nao_se_aplica", "cobre": ["premissas.produtividade.*"]})
    preco = pr["preco"]
    if preco.get("status") == "fonte":
        f = preco["fonte"]
        provs.append({"id": "preco", "fonte": f"{f['fonte']} — {f['indicador']}", "versao": f"cotação de {f['data']}",
                      "periodo": f["data"], "unidade": preco["unidade"], "localizacao": f["praca"],
                      "qualidade": preco.get("nota") or "indicador publicado", "situacao": "fonte", "url": f.get("url"),
                      "obtido_em": f.get("obtido_em"), "cobre": ["premissas.preco.*"]})
    elif preco.get("status") == "nao_se_aplica":
        provs.append({"id": "preco_nao_se_aplica", "fonte": "TELLUS economia (spec 007)", "versao": r["versao_premissas"],
                      "periodo": "não se aplica", "unidade": preco["unidade"], "localizacao": "não se aplica",
                      "qualidade": preco.get("motivo") or "não se aplica", "situacao": "nao_se_aplica", "cobre": ["premissas.preco.*"]})
    perc = pr["percentis"]
    if s is not None:
        chuva = s["entradas"]["clima"]["proveniencia"]["chuva"]
        provs.append({"id": "perda_motor", "fonte": "TELLUS motor hídrico (spec 006), quantis da perda relativa FAO-33",
                      "versao": s["versao_entradas"], "periodo": _periodo(chuva.get("periodo")), "unidade": "fração 0–1",
                      "localizacao": _s(chuva.get("localizacao")),
                      "qualidade": f"{s['resultado']['anos_validos']} anos válidos; frequência histórica, não previsão",
                      "situacao": "calculado", "cobre": ["cenarios.*.perda_relativa"]})
        provs.append({"id": "percentis", "fonte": "D-006 (hipótese do TELLUS, editável)", "versao": _s(perc["valores"]),
                      "periodo": _periodo(chuva.get("periodo")), "unidade": "percentil da perda relativa",
                      "localizacao": "não se aplica (regra de leitura dos cenários)", "qualidade": f"hipotese — {perc['descricao']}",
                      "situacao": "hipotese", "cobre": ["cenarios.*.percentil_perda"]})
    provs.append({"id": "calculo_margem", "fonte": f"TELLUS economia (spec 007): {r['formula']}", "versao": r["versao_premissas"],
                  "periodo": cc["mes_referencia"] if cc else "não se aplica", "unidade": "kg/ha, sacas/ha, R$/ha",
                  "localizacao": local_praca or "não se aplica",
                  "qualidade": "calculado com as premissas acima" + ("; inclui premissas do produtor" if r["alteracoes"] else ""),
                  "situacao": "calculado",
                  "cobre": ["cenarios.*.produtividade_kg_ha", "cenarios.*.sacas_ha", "cenarios.*.receita_r_ha",
                            "cenarios.*.margem_r_ha", "comparacao.*"]})
    if r["alteracoes"]:
        provs.append({"id": "premissas_do_produtor", "fonte": "Produtor (premissas_editadas do pedido)", "versao": r["versao_premissas"],
                      "periodo": "não se aplica (valor informado)", "unidade": "ver unidade de cada alteração",
                      "localizacao": "lavoura do pedido", "qualidade": "informado pelo produtor; o valor anterior fica ao lado",
                      "situacao": "editado", "cobre": ["alteracoes.*", "premissas.*.valor_usado", "premissas.custo.valor_usado_r_ha",
                                "custo_conab.itens.*.valor_usado_r_ha", "cenarios.*.custo_r_ha"]})
    if cotacao and cotacao.get("origem_informada") and cotacao.get("data_informada"):
        alt = next((x for x in r["alteracoes"] if x.get("premissa") == "preco_r_saca"), {})
        origem = alt.get("origem_informada") or cotacao["origem_informada"]
        data = str(alt.get("data_informada") or cotacao["data_informada"])
        provs.append({"id": "preco_informado", "fonte": origem, "versao": f"cotação informada em {data}", "periodo": data,
                      "unidade": cotacao.get("unidade") or preco["unidade"], "localizacao": origem,
                      "qualidade": "informada pelo produtor; sem indicador oficial (D-005)",
                      "situacao": "informada_pelo_produtor", "obtido_em": data,
                      "cobre": ["premissas.preco.valor_usado", "alteracoes.*"]})
    avisos = [_aviso("margem_indisponivel", m, "spec 007") for m in r["motivos_indisponivel"]]
    if perc.get("status") == "hipotese":
        avisos.append(_aviso("percentis_hipotese", perc["descricao"], "spec 007 (D-006)"))
    return {
        "id": "economia", "spec": "007 (#46)", "obrigatoria": True,
        "estado": "disponivel" if r["margem_disponivel"] else "indisponivel",
        "versao_modulo": r["versao_premissas"], "conteudo": dict(r), "proveniencia": provs, "avisos": avisos, "erro": None,
    }


def secao_com_erro(id_: str, spec: str, erro: dict, conteudo: dict | None = None) -> dict:
    return {"id": id_, "spec": spec, "obrigatoria": True, "estado": "erro", "versao_modulo": None, "conteudo": conteudo,
            "proveniencia": [], "avisos": [], "erro": erro}


def secao_indisponivel(id_: str, spec: str, codigo: str, mensagem: str) -> dict:
    return {"id": id_, "spec": spec, "obrigatoria": True, "estado": "indisponivel", "versao_modulo": None, "conteudo": None,
            "proveniencia": [], "avisos": [_aviso(codigo, mensagem, f"spec {spec}")], "erro": None}


def secao_recomendacao_pendente() -> dict:
    return {"id": "recomendacao", "spec": "008 (#48)", "obrigatoria": True, "estado": "pendente", "versao_modulo": None,
            "conteudo": None, "proveniencia": [], "avisos": [_aviso("secao_pendente", AVISO_008, "spec 008")], "erro": None}


# ---------------------------------------------------------------- contextos (#99)


def contexto(id_: str, solicitado: bool, valor: Mapping | None) -> dict:
    spec = {"vegetacao": "009 (#50)", "umidade": "010 (#52)"}[id_]
    if not solicitado:
        return {"id": id_, "spec": spec, "estado": "nao_solicitado", "conteudo": None, "avisos": [], "erro": None}
    if valor is None:
        return {"id": id_, "spec": spec, "estado": "indisponivel", "conteudo": None,
                "avisos": [_aviso("contexto_nao_integrado", f"O módulo da spec {spec} não respondeu nesta instalação.", f"spec {spec}")],
                "erro": None}
    if "erro" in valor and isinstance(valor["erro"], Mapping):
        e = valor["erro"]
        return {"id": id_, "spec": spec, "estado": "erro", "conteudo": None, "avisos": [],
                "erro": {"tipo": "erro", "codigo": e.get("codigo", "erro"), "mensagem": e.get("mensagem", ""),
                         "origem": e.get("origem") or f"spec {spec}", "campo": e.get("campo"),
                         "cache": {"disponivel": False, "obtido_em": None}, "acao": "O resultado principal não depende deste contexto."}}
    return {"id": id_, "spec": spec, "estado": "disponivel", "conteudo": dict(valor),
            "avisos": list(valor.get("avisos", [])), "erro": None}


# ---------------------------------------------------------------- montagem (#97, #98)


def montar_resposta(pedido: Mapping, blocos: list[dict], contextos: Mapping[str, dict], fontes: list[dict],
                    erros: list[dict], hipoteses: list[str], premissas: list[dict]) -> dict:
    recomendacao = secao_recomendacao_pendente()
    principal = {"culturas": blocos, "recomendacao": recomendacao}
    todas = [b[n] for b in blocos for n in ("risco_hidrico", "economia")] + [recomendacao]
    estado = regras.estado_geral(todas, fontes)
    avisos = [_aviso("secao_pendente", AVISO_008, "spec 008")]
    if estado == "final_com_cache" or any(f["estado"] == "cache" for f in fontes):
        datas = sorted({f["obtido_em"] for f in fontes if f["estado"] == "cache" and f["obtido_em"]})
        avisos.append(_aviso("cache_usado", "Parte dos dados veio de cópia guardada (cache) de " + ", ".join(datas) + ".", "fontes"))
    if estado == "erro":
        avisos.append(_aviso("sem_resultado_final", "Uma fonte obrigatória falhou sem cópia guardada: nenhum número desta resposta é final.", "contrato"))
    return {
        "versao_contrato": VERSAO, "pedido": dict(pedido), "estado_geral": estado, "final": estado in ("final", "final_com_cache"),
        **principal,
        "contextos": {k: contextos[k] for k in ("vegetacao", "umidade")},
        "fontes": fontes, "avisos": avisos, "erros": erros, "hipoteses": sorted(set(hipoteses)), "premissas_editadas": premissas,
        "versoes": {"contrato": VERSAO, "hash_pedido": pedido["hash_pedido"], "hash_principal": regras.hash_estavel(principal),
                    "modulos": {f"{b['cultura']}.{n}": b[n]["versao_modulo"] for b in blocos for n in ("risco_hidrico", "economia")}},
    }


# ---------------------------------------------------------------- execução com os módulos reais (exemplos e testes)


def erro_tempo_excedido(prazo_s: float, decorrido_s: float) -> versao.ErroContrato:
    """D-009: processamento síncrono com prazo; sem fila. Erro com código, origem e sugestão."""
    return versao.ErroContrato(
        "tempo_excedido",
        f"O cálculo passou do prazo de {prazo_s:g} s (parou em {decorrido_s:.1f} s) e foi interrompido; nenhum resultado parcial "
        "é devolvido. Tente de novo: os dados já baixados ficam em cache e a segunda chamada é mais rápida. "
        "Se persistir, reduza a área ou peça uma cultura por vez.",
        origem="contrato (processamento síncrono, D-009)", status=504)


def calcular(pedido: Mapping, contextos_respostas: Mapping[str, Mapping | None] | None = None,
             simular: Callable[[dict], dict] | None = None, margem: Callable[..., dict] | None = None,
             prazo_s: float | None = None, relogio: Callable[[], float] | None = None) -> dict:
    """Executa 006 e 007 para o pedido normalizado. Não é exposto como rota nesta versão (a 008 falta).

    `simular`/`margem` permitem injetar falhas nos testes; por padrão são os módulos reais.
    Prazo (D-009): conferido depois de cada chamada de módulo (interrupção cooperativa; uma chamada
    isolada mais longa que o prazo só é detectada ao terminar). `relogio` é injetável para teste.
    """
    import time

    prazo_s = regras.limites()["processamento_prazo_s"]["valor"] if prazo_s is None else prazo_s
    relogio = relogio or time.monotonic
    inicio = relogio()

    def conferir_prazo() -> None:
        decorrido = relogio() - inicio
        if decorrido > prazo_s:
            raise erro_tempo_excedido(prazo_s, decorrido)

    from tellus.car import regras as car_regras
    from tellus.economia import servico as economia
    from tellus.motor import servico as motor

    simular = simular or motor.simular
    margem = margem or economia.margem
    a = pedido["area"]
    lat, lon = (a["lat"], a["lon"]) if a["tipo"] == "ponto" else car_regras.centroide_bbox(a["geometria"])
    culturas = [pedido["cultura"]] if pedido["metodologia"] == "cultura_escolhida" else list(CULTURAS)
    edits = pedido.get("premissas_editadas", [])
    blocos, fontes, erros, hipoteses, premissas_saida = [], [], [], [], []
    for c in culturas:
        mine = [p for p in edits if p.get("cultura") in (None, c)]
        ed_motor = {p["id"]: p["valor_novo"] for p in mine if p["modulo"] == "culturas"}
        ped_motor = {"lat": lat, "lon": lon, "cultura": c, "grupo": pedido["grupo"],
                     "solo": {k: v for k, v in pedido["solo"].items() if v is not None},
                     "data_colheita_soja": pedido["data_colheita_soja"]}
        if a["tipo"] == "ponto" and a.get("codigo_ibge"):
            ped_motor["codigo_ibge"] = a["codigo_ibge"]
        for p in mine:
            if p["modulo"] == "motor" and p["id"] == "armazenamento_inicial_frac":
                ped_motor["armazenamento_inicial_frac"] = p["valor_novo"]
            elif p["modulo"] == "motor" and p["id"] == "entressafra.kc":
                ped_motor["entressafra"] = {"kc": p["valor_novo"]}
        if ed_motor:
            ped_motor["edicoes"] = ed_motor
        s = None
        if pedido["grupo"] == "nao_sei":
            rh = secao_indisponivel("risco_hidrico", "006 (#44)", "grupo_nao_sei",
                                    "Grupo 'não sei' exige um cálculo por grupo e a comparação entre eles, papel da recomendação (008, pendente).")
        else:
            try:
                s = simular(ped_motor)
                conferir_prazo()
                rh, f, h = secao_risco_hidrico(s)
                fontes += f
                hipoteses += h
            except versao.ErroContrato:
                raise
            except Exception as exc:  # noqa: BLE001 — qualquer erro de módulo vira ErroFonte legível
                e = erro_fonte(exc, "spec 006 (motor hídrico)", acao="Sem estes dados o risco e a margem desta cultura não são calculados.")
                erros.append(e)
                fontes.append({"fonte": e["origem"], "estado": "falha", "obtido_em": None, "secao": "risco_hidrico"})
                rh = secao_com_erro("risco_hidrico", "006 (#44)", e)
        ed_econ = {p["id"]: p["valor_novo"] for p in mine if p["modulo"] == "economia"}
        if rh["estado"] == "erro":
            ec = secao_indisponivel("economia", "007 (#46)", "dependencia_com_erro",
                                    "A margem depende do risco hídrico desta cultura, que falhou.")
        else:
            try:
                perdas = s["resultado"]["perda_relativa_quantis"] if s else None
                r = margem(lat, lon, c, perdas, ed_econ or None)
                conferir_prazo()
                cot = next((p for p in mine if p["modulo"] == "economia" and p["id"] == "preco_r_saca" and p.get("origem_informada")), None)
                ec = secao_economia(r, s, cot)
            except versao.ErroContrato:
                raise
            except Exception as exc:  # noqa: BLE001
                e = erro_fonte(exc, "spec 007 (economia)")
                erros.append(e)
                ec = secao_com_erro("economia", "007 (#46)", e)
        for p in mine:
            padrao = None
            if p["modulo"] == "economia" and ec.get("conteudo"):
                padrao = next((x["valor_anterior"] for x in ec["conteudo"].get("alteracoes", []) if x["premissa"] == p["id"]), None)
            elif p["modulo"] == "culturas" and s:
                padrao = next((x["valor_anterior"] for x in s["entradas"]["cultura"]["alteracoes"] if x["parametro"] == p["id"]), None)
            elif p["modulo"] == "motor" and s and p["id"] == "armazenamento_inicial_frac":
                padrao = motor.PREMISSAS["estado_inicial"]["valor"]
            elif p["modulo"] == "motor" and s and p["id"] == "entressafra.kc":
                padrao = s["entradas"]["entressafra"].get("kc_padrao")
            premissas_saida.append(dict(p) | {"cultura": c, "valor_padrao": padrao if isinstance(padrao, (int, float)) else None})
        blocos.append({"cultura": c, "risco_hidrico": rh, "economia": ec})
    pedido_ctx = pedido.get("contextos") or {}
    ctx = {k: contexto(k, bool(pedido_ctx.get(k)), (contextos_respostas or {}).get(k)) for k in ("vegetacao", "umidade")}
    return montar_resposta(pedido, blocos, ctx, fontes, erros, hipoteses, premissas_saida)
