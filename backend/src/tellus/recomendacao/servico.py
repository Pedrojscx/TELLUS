"""Recomendação com duas metodologias sobre o MESMO motor (spec 008).

- cultura_escolhida: decêndios permitidos de uma cultura, ordenados.
- calculo_completo: a mesma avaliação para cada cultura, juntada e ordenada.
A recomendação só filtra e ordena; os valores vêm do motor (006), do ZARC (004) e da economia (007).
"""

from __future__ import annotations

import copy

from tellus.economia import servico as economia
from tellus.motor import servico as motor
from tellus.zarc import servico as zarc

CULTURAS = ["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"]
CRITERIO = [
    {"campo": "margem_r_ha.conservador", "direcao": "decrescente", "descricao": "maior margem no cenário conservador"},
    {"campo": "risco_historico_falha_severa", "direcao": "crescente", "descricao": "menor risco histórico de falha severa"},
    {"campo": "risco_zarc_pct", "direcao": "crescente", "descricao": "menor risco oficial do ZARC"},
    {"campo": "decendio", "direcao": "crescente", "descricao": "plantio mais cedo"},
    {"campo": "cultura", "direcao": "alfabética", "descricao": "desempate final"},
]
DECISAO_PERCENTIS = ("D-006: cenários pelos quartis da perda simulada — conservador = percentil 75 (pior em 1 de cada 4 anos), "
                     "central = mediana, favorável = percentil 25. Decisão de produto, sem fonte setorial; editável.")


class ErroRecomendacao(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


def _grupos_zarc(pedido: dict, cultura: str) -> list[str]:
    """Grupo informado, ou todos os grupos do ZARC quando 'não sei' (None)."""
    if pedido.get("grupo"):
        return [pedido["grupo"]]
    e = motor.preparar(_pedido_motor(pedido, cultura, "GRUPO I"))
    cal = zarc.calendario(e["codigo_ibge"], motor.CULTURA_ZARC[cultura], None, e["solo"]["classe"])
    return [g["grupo"] for g in cal.get("grupos", []) if g.get("disponivel")] or ["GRUPO I"]


def _pedido_motor(pedido: dict, cultura: str, grupo: str) -> dict:
    base = {k: copy.deepcopy(v) for k, v in pedido.items()
            if k in ("lat", "lon", "codigo_ibge", "solo", "data_colheita_soja", "entressafra", "armazenamento_inicial_frac",
                     "geometria", "id_geometria")}
    ed = (pedido.get("edicoes_cultura") or {}).get(cultura)
    return base | {"cultura": cultura, "grupo": grupo} | ({"edicoes": ed} if ed else {})


def _hipoteses(sim: dict, eco: dict) -> list[str]:
    hip = []
    for a in sim["avisos"]:
        if a["codigo"] == "hipoteses":
            hip.append(a["mensagem"])
    if eco["premissas"]["percentis"]["status"] == "hipotese":
        hip.append("Percentis dos cenários (D-006)")
    if eco["estado"] == "com_premissas_do_produtor":
        hip.append("Premissas econômicas editadas pelo produtor")
    return hip


def avaliar_cultura(pedido: dict, cultura: str) -> dict:
    """Todas as alternativas (grupo × decêndio da janela ZARC) de uma cultura, com valores do motor e da economia."""
    if cultura not in CULTURAS:
        raise ErroRecomendacao("cultura_invalida", f"Cultura deve ser uma de {CULTURAS}.", "cultura")
    alternativas, indisponiveis = [], []
    try:
        grupos = _grupos_zarc(pedido, cultura)
    except (motor.ErroMotor, Exception) as e:  # noqa: BLE001 — erro de domínio vira indisponibilidade da cultura
        return {"cultura": cultura, "grupos_testados": [], "alternativas": [],
                "indisponiveis": [{"cultura": cultura, "motivo": getattr(e, "mensagem", str(e))}]}
    ed_eco = (pedido.get("edicoes_economia") or {}).get(cultura)
    for grupo in grupos:
        pm = _pedido_motor(pedido, cultura, grupo)
        try:
            jan = motor.simular_janela(pm)
        except motor.ErroMotor as e:
            indisponiveis.append({"cultura": cultura, "grupo": grupo, "motivo": e.mensagem})
            continue
        for d in jan["decendios"]:
            if d["situacao"] != "simulado":
                indisponiveis.append({"cultura": cultura, "grupo": grupo, "decendio": d["decendio"],
                                      "motivo": "decêndio da janela termina antes da colheita da soja"})
                continue
            sim = motor.simular(pm | {"data_plantio": d["data_plantio"]})
            eco = economia.margem(sim["pedido"]["lat"], sim["pedido"]["lon"], cultura,
                                  sim["resultado"]["perda_relativa_quantis"], ed_eco, pedido.get("percentis"))
            alt = {
                "cultura": cultura,
                "grupo": grupo,
                "decendio": d["decendio"],
                "data_plantio": sim["pedido"]["data_plantio"],
                "risco_zarc_pct": sim["resultado"]["risco_zarc_pct"],
                "portaria_zarc": sim["entradas"]["zarc"]["portaria"],
                "risco_historico_falha_severa": sim["resultado"]["risco_historico_falha_severa"],
                "anos_validos": sim["resultado"]["anos_validos"],
                "deficit_mm_mediano": sim["resultado"]["deficit_mm_mediano"],
                "perda_relativa_quantis": sim["resultado"]["perda_relativa_quantis"],
                "margem_disponivel": eco["margem_disponivel"],
                "margem_r_ha": {k: v["margem_r_ha"] for k, v in eco["cenarios"].items()},
                "cenarios": eco["cenarios"],
                "unidades": {"margem_r_ha": "R$/ha", "risco_historico_falha_severa": "fração dos anos", "risco_zarc_pct": "%",
                             "deficit_mm_mediano": "mm"},
                "versoes": {"motor": sim["versao_entradas"], "economia": eco["versao_premissas"]},
                "hipoteses": _hipoteses(sim, eco),
                "motivos_indisponivel": eco["motivos_indisponivel"],
            }
            (alternativas if eco["margem_disponivel"] else indisponiveis).append(
                alt if eco["margem_disponivel"] else alt | {"motivo": "; ".join(eco["motivos_indisponivel"])})
    return {"cultura": cultura, "grupos_testados": grupos, "alternativas": alternativas, "indisponiveis": indisponiveis}


def _chave(a: dict) -> tuple:
    return (-a["margem_r_ha"]["conservador"], a["risco_historico_falha_severa"], a["risco_zarc_pct"] or 0, a["decendio"], a["cultura"], a["grupo"])


def ordenar(alternativas: list[dict]) -> list[dict]:
    """Ordem pública (CRITERIO). Só alternativas completas e dentro do ZARC chegam aqui."""
    ordenadas = sorted(alternativas, key=_chave)
    return [a | {"posicao": i + 1} for i, a in enumerate(ordenadas)]


def recomendar(pedido: dict) -> dict:
    metodologia = pedido.get("metodologia")
    if metodologia == "cultura_escolhida":
        if pedido.get("cultura") not in CULTURAS:
            raise ErroRecomendacao("cultura_obrigatoria", f"Na cultura escolhida, informe cultura: {CULTURAS}.", "cultura")
        culturas = [pedido["cultura"]]
    elif metodologia == "calculo_completo":
        culturas = CULTURAS
    else:
        raise ErroRecomendacao("metodologia_invalida", "metodologia deve ser 'cultura_escolhida' ou 'calculo_completo'.", "metodologia")
    avaliacoes = [avaliar_cultura(pedido, c) for c in culturas]
    completas = [a for av in avaliacoes for a in av["alternativas"]]
    ranking = ordenar(completas)
    indisponiveis = [i for av in avaliacoes for i in av["indisponiveis"]]
    recomendada = ranking[0] if ranking else None
    avisos = [{"codigo": "nao_e_previsao", "mensagem": motor.AVISO_HISTORICO},
              {"codigo": "riscos_distintos", "mensagem": "risco_zarc_pct é o risco oficial da portaria; risco_historico_falha_severa é "
                                                         "a frequência simulada pelo TELLUS; margem_r_ha é econômica. São medidas distintas."},
              {"codigo": "percentis", "mensagem": DECISAO_PERCENTIS}]
    if not ranking:
        avisos.append({"codigo": "sem_recomendacao", "mensagem": "Nenhuma combinação tem dados completos dentro da janela ZARC; não há recomendação. Veja 'indisponiveis'."})
    return {
        "metodologia": metodologia,
        "criterio_ordem": CRITERIO,
        "grupos_testados": {av["cultura"]: av["grupos_testados"] for av in avaliacoes},
        "grupo_informado": pedido.get("grupo"),
        "recomendada": recomendada,
        "alternativas": ranking,
        "indisponiveis": indisponiveis,
        "avisos": avisos,
    }
