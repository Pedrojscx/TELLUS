"""Leitura da planilha de custo de produção da Conab (uma aba por praça-ano). Puro sobre as linhas."""

from __future__ import annotations

import re

# rótulos de totais da planilha → chave e itens que eles somam
TOTAIS = {
    "TOTAL DAS DESPESAS DE CUSTEIO (A)": "custeio",
    "TOTAL DAS OUTRAS DESPESAS (B)": "outras_despesas",
    "TOTAL DAS DESPESAS FINANCEIRAS (C)": "despesas_financeiras",
    "CUSTO VARIÁVEL (A+B+C=D)": "custo_variavel",
    "TOTAL DE DEPRECIAÇÕES (E)": "depreciacoes",
    "TOTAL DE OUTROS CUSTOS FIXOS (F)": "outros_custos_fixos",
    "CUSTO FIXO (E+F=G)": "custo_fixo",
    "CUSTO OPERACIONAL (D+G=H)": "custo_operacional",
    "TOTAL DE RENDA DE FATORES (F)": "renda_fatores",
    "CUSTO TOTAL (H+I=J)": "custo_total",
}
GRUPO_SECAO = {"I": "custeio", "II": "outras_despesas", "III": "despesas_financeiras", "IV": "depreciacoes",
               "V": "outros_custos_fixos", "VI": "renda_fatores"}
# nível de custo → grupos de itens incluídos
NIVEIS = {
    "custeio": ["custeio"],
    "custo_variavel": ["custeio", "outras_despesas", "despesas_financeiras"],
    "custo_operacional": ["custeio", "outras_despesas", "despesas_financeiras", "depreciacoes", "outros_custos_fixos"],
    "custo_total": ["custeio", "outras_despesas", "despesas_financeiras", "depreciacoes", "outros_custos_fixos", "renda_fatores"],
}
MESES = {"janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
         "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


class ErroPlanilha(Exception):
    pass


def ler_aba(linhas: list[list]) -> dict:
    """`linhas`: valores das células, linha a linha, como devolvidos pelo xlrd."""
    txt = [[str(c).strip() for c in l] for l in linhas]
    cab = [next((c for c in l if c), "") for l in txt[:8]]
    titulo = next((c for c in cab if c.upper().startswith("AGRICULTURA")), "")
    mes_ano = next((c for c in cab if c.lower().startswith("mês/ano") or c.lower().startswith("mes/ano")), "")
    prod = next((c for c in cab if c.lower().startswith("produtividade")), "")
    m = re.search(r"([A-Za-zçÇ]+)/(\d{4})", mes_ano)
    if not m:
        raise ErroPlanilha(f"mês de referência não encontrado: {mes_ano!r}")
    mes_ref = f"{m.group(2)}-{MESES[m.group(1).lower()]:02d}"
    mp = re.search(r"([\d.]+,\d+|\d+)\s*(kg/)?ha", prod)
    if not mp:
        raise ErroPlanilha(f"produtividade não encontrada: {prod!r}")
    avisos = [] if mp.group(2) else [f"a planilha não traz a unidade da produtividade ({prod!r}); assumido kg/ha, como nas demais abas"]
    produtividade = float(mp.group(1).replace(".", "").replace(",", "."))
    sistema = titulo.split(" - ")[2].strip() if titulo.count(" - ") >= 2 else None
    itens, totais = [], {}
    grupo = None
    inicio = next((i + 1 for i, l in enumerate(txt) if l and l[0].upper().startswith("DISCRIMINA")), None)
    if inicio is None:
        raise ErroPlanilha("cabeçalho DISCRIMINAÇÃO não encontrado")
    for l in txt[inicio:]:
        nome = l[0] if l else ""
        if not nome:
            continue
        sec = re.match(r"^(I|II|III|IV|V|VI) - ", nome)
        if sec:
            grupo = GRUPO_SECAO[sec.group(1)]
            continue
        if nome in TOTAIS:
            totais[TOTAIS[nome]] = round(float(l[1]), 2)
            continue
        mi = re.match(r"^(\d+(?:\.\d+)?) - (.+?):?$", nome)
        if mi and len(l) > 1 and l[1] not in ("", None):
            try:
                valor = float(l[1])
            except ValueError:
                continue
            itens.append({"codigo": mi.group(1), "nome": mi.group(2).strip(), "grupo": grupo, "valor_r_ha": round(valor, 2)})
    faltam = [k for k in TOTAIS.values() if k not in totais]
    if faltam:
        raise ErroPlanilha(f"totais ausentes na planilha: {faltam}")
    return {"titulo": titulo, "sistema": sistema, "mes_referencia": mes_ref, "produtividade_kg_ha": produtividade,
            "tipo_produtividade": "ex-ante (premissa da Conab)", "itens": itens, "totais": totais, "avisos": avisos}


def conferir(planilha: dict, tolerancia: float = 0.1) -> list[str]:
    """Recompõe os totais pelos itens; devolve as divergências (vazio = confere)."""
    erros = []
    soma = {}
    for it in planilha["itens"]:
        soma[it["grupo"]] = soma.get(it["grupo"], 0.0) + it["valor_r_ha"]
    for g in ("custeio", "outras_despesas", "despesas_financeiras", "depreciacoes", "outros_custos_fixos", "renda_fatores"):
        if abs(soma.get(g, 0.0) - planilha["totais"][g]) > tolerancia:
            erros.append(f"{g}: itens somam {soma.get(g, 0.0):.2f}, total {planilha['totais'][g]:.2f}")
    t = planilha["totais"]
    for nivel, grupos in NIVEIS.items():
        if abs(sum(t[g] for g in grupos) - t[nivel]) > tolerancia:
            erros.append(f"{nivel}: grupos somam {sum(t[g] for g in grupos):.2f}, total {t[nivel]:.2f}")
    return erros


def custo_do_nivel(planilha: dict, nivel: str, ajustes: dict[str, float] | None = None) -> tuple[float, list[dict]]:
    """Custo (R$/ha) do nível e a lista de itens incluídos, com ajustes do produtor por código de item."""
    if nivel not in NIVEIS:
        raise ValueError(f"nível de custo deve ser um de {list(NIVEIS)}")
    ajustes = ajustes or {}
    incluidos = []
    for it in planilha["itens"]:
        if it["grupo"] in NIVEIS[nivel]:
            novo = ajustes.get(it["codigo"])
            incluidos.append(it | {"valor_usado_r_ha": round(novo if novo is not None else it["valor_r_ha"], 2),
                                   "editado": novo is not None})
    return round(sum(i["valor_usado_r_ha"] for i in incluidos), 2), incluidos
