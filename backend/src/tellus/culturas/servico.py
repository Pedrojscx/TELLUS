"""Premissas de solo e cultura com fonte ou hipótese, validade regional e edição do produtor (spec 005)."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from . import solo

RAIZ = Path(__file__).resolve().parents[4]
BASE = json.loads((RAIZ / "referencias" / "culturas" / "parametros.json").read_text(encoding="utf-8"))

# domínio físico aceito para edição (Princípio V: valor incompatível dá erro, sem ajuste silencioso)
DOMINIO = {
    "ze_cm": (10, 300),
    "cad_mm": (5, 300),
    "fases_dias": (1, 150),
    "ciclo_dias": (0, 250),
    "isna_limite": (0.0, 1.0),
    "kc": (0.1, 1.6),
    "ky": (0.0, 2.5),
    "p_esgotamento": (0.1, 0.9),
}


class ErroPremissa(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


def culturas() -> dict:
    return {k: {"nome": v["nome"], "classificacao_solo": v["classificacao_solo"], "nota": v.get("nota")}
            for k, v in BASE["culturas"].items()}


def _cultura(cultura: str) -> dict:
    if cultura not in BASE["culturas"]:
        raise ErroPremissa("cultura_invalida", f"Cultura desconhecida: {cultura}. Use uma de {sorted(BASE['culturas'])}.", "cultura")
    return BASE["culturas"][cultura]


def _fonte(chave: str | None) -> dict | None:
    return None if not chave else {"id": chave, **BASE["fontes"][chave]}


def _resolver(p: dict, uf: str | None) -> dict:
    """Parâmetro com fonte completa ou hipótese; fora da validade regional, vira hipótese com motivo."""
    fonte = _fonte(p.get("fonte"))
    status = p["status"]
    motivo = p.get("motivo")
    if fonte and uf:
        ufs = fonte["validade_regional"]["uf"]
        if "*" not in ufs and uf not in ufs:
            status = "hipotese"
            motivo = (f"A fonte vale para {', '.join(ufs)}; aplicada em {uf} fora da validade regional "
                      f"até haver a portaria equivalente da UF.")
    return {
        "id": p["id"],
        "nome": p["nome"],
        "unidade": p["unidade"],
        "valor_padrao": p["valor"],
        "valor_usado": copy.deepcopy(p["valor"]),
        "editado": False,
        "status": status,
        "fonte": fonte,
        "trecho": p.get("trecho"),
        "metodo_referencia": p.get("metodo_referencia"),
        "motivo": motivo,
    }


def parametros(cultura: str, uf: str | None = None) -> dict:
    c = _cultura(cultura)
    return {
        "cultura": cultura,
        "nome": c["nome"],
        "uf": uf,
        "nota": c.get("nota"),
        "metodos_referencia": BASE["metodos_referencia"],
        "parametros": [_resolver(p, uf) for p in c["parametros"]],
    }


def _validar(pid: str, valor, chave: str | None) -> None:
    lo, hi = DOMINIO.get(pid, (None, None))
    valores = valor if isinstance(valor, list) else [valor]
    for v in valores:
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            raise ErroPremissa("valor_invalido", f"{pid}{'.' + chave if chave else ''}: valor precisa ser numérico.", pid)
        if lo is not None and not lo <= v <= hi:
            raise ErroPremissa("fora_do_dominio", f"{pid}{'.' + chave if chave else ''} = {v} fora do domínio aceito ({lo} a {hi}).", pid)


def premissas(cultura: str, uf: str | None = None, edicoes: dict | None = None) -> dict:
    """Aplica edições do produtor no formato {"kc.med": 1.1, "ze_cm": 70, "fases_dias.GRUPO I": [..]}."""
    res = parametros(cultura, uf)
    por_id = {p["id"]: p for p in res["parametros"]}
    alteracoes = []
    for caminho, novo in (edicoes or {}).items():
        pid, _, chave = caminho.partition(".")
        if pid not in por_id:
            raise ErroPremissa("parametro_desconhecido", f"Parâmetro desconhecido: {pid}.", caminho)
        p = por_id[pid]
        _validar(pid, novo, chave or None)
        if chave:
            if not isinstance(p["valor_usado"], dict) or chave not in p["valor_usado"]:
                raise ErroPremissa("parametro_desconhecido", f"{pid} não tem o item {chave}.", caminho)
            anterior = p["valor_usado"][chave]
            if isinstance(anterior, list) and (not isinstance(novo, list) or len(novo) != len(anterior)):
                raise ErroPremissa("valor_invalido", f"{caminho} precisa de {len(anterior)} valores.", caminho)
            p["valor_usado"][chave] = novo
        else:
            if isinstance(p["valor_usado"], dict):
                raise ErroPremissa("valor_invalido", f"{pid} tem itens; edite um deles (ex.: {pid}.{next(iter(p['valor_usado']))}).", caminho)
            anterior = p["valor_usado"]
            p["valor_usado"] = novo
        p["editado"] = True
        alteracoes.append({"parametro": caminho, "valor_anterior": anterior, "valor_novo": novo, "unidade": p["unidade"],
                           "origem_novo": "produtor"})
    return res | {"alteracoes": alteracoes}


# ----------------------------------------------------------------- solo


def _textura_sibcs(areia: float, argila: float) -> str:
    """Classe textural aproximada (SiBCS) a partir da granulometria — usada só como hipótese no sorgo."""
    if argila >= 35:
        return "argilosa"
    if areia - argila >= 70:
        return "arenosa"
    return "media"


def classificar_solo(cultura: str, uf: str | None = None, textura: str | None = None, granulometria: dict | None = None,
                     classe: str | None = None, cad_mm: float | None = None) -> dict:
    """Classe de solo e CAD em mm para a cultura, a partir de UMA das entradas (precedência: cad_mm, classe,
    granulometria, textura). Indica origem e status (fonte/hipótese) de cada passo."""
    c = _cultura(cultura)
    params = {p["id"]: p for p in parametros(cultura, uf)["parametros"]}
    cad_tabela = params["cad_mm"]["valor_padrao"]
    ze = params["ze_cm"]["valor_padrao"]
    status_cad = params["cad_mm"]["status"]
    passos = []
    tipo = c["classificacao_solo"]
    if cad_mm is not None:
        _validar("cad_mm", cad_mm, None)
        ad = cad_mm / ze
        cl = solo.classe_ad(ad) if tipo == "AD" else None
        return {"cultura": cultura, "classe": cl, "cad_mm": round(float(cad_mm), 1), "ad_mm_cm": round(ad, 3),
                "origem": "produtor", "status": "editado", "passos": [{"passo": "CAD informada pelo produtor", "status": "editado"}],
                "aviso": None if cl or tipo != "AD" else "Valor abaixo da menor classe do ZARC (AD1 ≥ 0,34 mm/cm)."}
    if classe is None and granulometria is not None:
        g = {k: granulometria.get(k) for k in ("areia", "silte", "argila")}
        try:
            ad = solo.agua_disponivel_mm_cm(g["areia"], g["silte"], g["argila"])
        except (TypeError, ValueError) as e:
            raise ErroPremissa("granulometria_invalida", str(e), "granulometria")
        if tipo == "AD":
            classe = solo.classe_ad(ad)
            passos.append({"passo": f"AD = {ad:.3f} mm/cm pela equação do Art. 3º", "status": "fonte", "fonte": _fonte("IN1_2022")})
            if classe is None:
                return {"cultura": cultura, "classe": None, "cad_mm": None, "ad_mm_cm": round(ad, 3), "origem": "granulometria",
                        "status": "indisponivel", "passos": passos,
                        "aviso": "AD abaixo de 0,34 mm/cm: fora das classes do ZARC. Informe a CAD em mm se tiver laudo."}
        else:
            textura = _textura_sibcs(g["areia"], g["argila"])
            passos.append({"passo": f"Textura '{textura}' estimada da granulometria (regra SiBCS simplificada)", "status": "hipotese"})
    if classe is None and textura is not None:
        if textura not in ("arenosa", "media", "argilosa"):
            raise ErroPremissa("textura_invalida", "Textura deve ser arenosa, media ou argilosa.", "textura")
        if tipo == "TIPO":
            classe = BASE["texturas"]["tipo_sorgo_oficial"][textura]
            passos.append({"passo": f"Textura {textura} = solo tipo {classe}", "status": status_cad, "fonte": params["cad_mm"]["fonte"]})
        else:
            g = BASE["texturas"]["granulometria_tipica_hipotese"][textura]
            ad = solo.agua_disponivel_mm_cm(g["areia"], g["silte"], g["argila"])
            classe = solo.classe_ad(ad)
            passos.append({"passo": f"Granulometria típica da textura {textura} ({g['areia']}/{g['silte']}/{g['argila']}% "
                                    f"areia/silte/argila), não medida", "status": "hipotese"})
            passos.append({"passo": f"AD = {ad:.3f} mm/cm pela equação do Art. 3º → {classe}", "status": "fonte", "fonte": _fonte("IN1_2022")})
    if classe is None:
        raise ErroPremissa("entrada_ausente", "Informe textura, granulometria, classe de solo ou CAD em mm.", "solo")
    if classe not in cad_tabela:
        raise ErroPremissa("classe_invalida", f"Classe {classe} não existe para {cultura}. Use uma de {sorted(cad_tabela)}.", "classe")
    passos.append({"passo": f"CAD da classe {classe} para {c['nome']}: {cad_tabela[classe]} mm", "status": status_cad,
                   "fonte": params["cad_mm"]["fonte"], "motivo": params["cad_mm"]["motivo"]})
    status = "hipotese" if any(p["status"] == "hipotese" for p in passos) else "fonte"
    origem = "classe" if not (textura or granulometria) else ("granulometria" if granulometria else "textura")
    aviso = None
    if origem == "textura" and tipo == "AD":
        aviso = "Classe estimada só pela textura (hipótese). Para usar a equação oficial, informe a análise granulométrica (0 a 40 cm)."
    return {"cultura": cultura, "classe": classe, "cad_mm": cad_tabela[classe],
            "ad_mm_cm": round(cad_tabela[classe] / ze, 3), "origem": origem, "status": status, "passos": passos, "aviso": aviso}
