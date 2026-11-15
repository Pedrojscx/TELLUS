"""Idioma das mensagens do backend (spec 014, FR-005 a FR-009; #113, #114).

O backend escreve as mensagens em português. Na saída da API, `traduzir_resposta` troca SÓ os campos de texto
legível (mensagem, ação, motivo, hipóteses, critério, notas...) pelo inglês do catálogo `en.json`. Códigos,
estados, números e valores do contrato nunca mudam: o mesmo pedido dá os mesmos números nos dois idiomas.

Catálogo:
- "exatos": frase em português → inglês.
- "modelos": [modelo_pt, modelo_en] com campos nomeados ({origem}, {data}). O valor do campo é copiado como veio
  (ex.: o nome da cooperativa informado pelo produtor). Campo terminado em `_lista` é uma lista separada por "; ",
  e cada item também passa pelo catálogo; campo terminado em `_t` é um texto que também passa pelo catálogo. Se um
  desses não tiver tradução, o modelo não vale (nunca devolve meia frase em português como se fosse inglês).
Texto em português sem tradução sai com o prefixo "(PT) " (FR-007), nunca vazio nem trocado por código.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

IDIOMAS = ("pt-BR", "en")
PADRAO = "pt-BR"
MARCA_SEM_TRADUCAO = "(PT) "

# Campos com texto para pessoas. Os demais (codigo, estado, cultura, unidade, origem_informada...) ficam intactos.
CAMPOS_TEXTO = frozenset({
    "mensagem", "acao", "motivo", "motivos_indisponivel", "hipoteses", "descricao", "nota", "notas", "pergunta",
    "periodo", "qualidade", "localizacao", "fonte", "regra", "temporal", "espacial", "espacial_texto", "escala",
    "limitacao", "uso", "texto", "natureza", "consulta", "detalhes", "risco_historico_falha_severa",
})

_PT = re.compile(r"[ãõçáéíóúâêôà]|\b(não|de|do|da|dos|das|com|sem|para|pelo|pela|uma|um|em|no|na|ao|que|é)\b", re.I)


def normalizar_idioma(valor: str | None) -> str:
    """'en', 'en-US', 'en-GB,en;q=0.9' → 'en'; qualquer outro → 'pt-BR'."""
    return "en" if (valor or "").strip().lower().startswith("en") else PADRAO


@lru_cache(maxsize=1)
def _catalogo() -> tuple[dict[str, str], list[tuple[re.Pattern[str], str, list[str]]]]:
    dados = json.loads((Path(__file__).with_name("en.json")).read_text(encoding="utf-8"))
    modelos = []
    for pt, en in dados["modelos"]:
        campos = re.findall(r"\{(\w+)\}", pt)
        partes = re.split(r"\{\w+\}", pt)
        rx = "".join(re.escape(p) + (f"(?P<{campos[i]}>.+?)" if i < len(campos) else "") for i, p in enumerate(partes))
        modelos.append((re.compile(f"^{rx}$", re.S), en, campos))
    return dados["exatos"], modelos


def parece_portugues(texto: str) -> bool:
    return " " in texto.strip() and bool(_PT.search(texto))


def _traduzir_ou_none(texto: str) -> str | None:
    exatos, modelos = _catalogo()
    t = texto.strip()
    if t in exatos:
        return exatos[t]
    for rx, en, campos in modelos:
        m = rx.match(t)
        if not m:
            continue
        valores = {}
        for c in campos:
            v = m.group(c)
            if c.endswith("_lista"):
                itens = [_traduzir_ou_none(x) for x in v.split("; ")]
                if any(i is None for i in itens):
                    break  # algum item sem tradução: tenta o próximo modelo / cai no fallback
                v = "; ".join(itens)  # type: ignore[arg-type]
            elif c.endswith("_t"):
                v = _traduzir_ou_none(v)
                if v is None:
                    break  # campo traduzível sem tradução: o modelo não serve
            valores[c] = v
        else:
            return en.format(**valores)
    return None


def traduzir(texto: str, idioma: str) -> str:
    """Um texto do backend no idioma pedido. Em português, devolve como está."""
    if normalizar_idioma(idioma) != "en" or not texto:
        return texto
    t = _traduzir_ou_none(texto)
    if t is not None:
        return t
    return MARCA_SEM_TRADUCAO + texto if parece_portugues(texto) else texto


def traduzir_resposta(obj: Any, idioma: str, _campo: str | None = None) -> Any:
    """Cópia da resposta com os campos de texto no idioma pedido (os outros campos intactos)."""
    if normalizar_idioma(idioma) != "en":
        return obj
    if isinstance(obj, dict):
        return {k: traduzir_resposta(v, idioma, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [traduzir_resposta(v, idioma, _campo) for v in obj]
    if isinstance(obj, str) and _campo in CAMPOS_TEXTO:
        return traduzir(obj, idioma)
    return obj


def sem_traducao(obj: Any, _campo: str | None = None) -> list[str]:
    """Textos em português de uma resposta que ainda não têm inglês no catálogo (teste de cobertura, SC-003)."""
    if isinstance(obj, dict):
        return [s for k, v in obj.items() for s in sem_traducao(v, k)]
    if isinstance(obj, list):
        return [s for v in obj for s in sem_traducao(v, _campo)]
    if isinstance(obj, str) and _campo in CAMPOS_TEXTO and parece_portugues(obj) and _traduzir_ou_none(obj) is None:
        return [obj]
    return []
