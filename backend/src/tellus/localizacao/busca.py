"""Busca de município por nome: sem acento, sem maiúsculas, parcial (FR-005)."""

from __future__ import annotations

import re
import unicodedata

LIMITE_PADRAO = 10
LIMITE_MAXIMO = 50


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def buscar(municipios_ordenados: list[dict], texto: str, limite: int = LIMITE_PADRAO) -> list[dict]:
    """Primeiro quem começa com o texto, depois quem contém; empate por nome e UF."""
    alvo = normalizar(texto)
    limite = max(1, min(limite, LIMITE_MAXIMO))
    comeca, contem = [], []
    for m in municipios_ordenados:
        nome = m["nome_normalizado"]
        if nome.startswith(alvo):
            comeca.append(m)
        elif alvo in nome:
            contem.append(m)
    return [
        {"codigo_ibge": m["codigo_ibge"], "nome": m["nome"], "uf": m["uf"]}
        for m in (comeca + contem)[:limite]
    ]
