"""Regras puras de solo: equação oficial de água disponível e classes AD (IN SPA/MAPA nº 1/2022)."""

from __future__ import annotations

import math

# Art. 2º: limites inferiores das classes AD1..AD6 em mm/cm (AD6: ≥ 1,40)
LIMITES_AD = [("AD1", 0.34), ("AD2", 0.46), ("AD3", 0.61), ("AD4", 0.80), ("AD5", 1.06), ("AD6", 1.40)]


def agua_disponivel_mm_cm(areia: float, silte: float, argila: float) -> float:
    """Art. 3º da IN SPA/MAPA nº 1/2022 (redação da IN nº 2/2022). Teores em %, camada 0 a 40 cm."""
    for nome, v in (("areia", areia), ("silte", silte), ("argila", argila)):
        if not (isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 100):
            raise ValueError(f"{nome} deve ser um percentual entre 0 e 100")
    if abs(areia + silte + argila - 100) > 2:
        raise ValueError("areia + silte + argila deve somar 100% (tolerância de 2 pontos)")
    at, sil, arg = areia, silte, argila
    x = (
        -0.02128887 * at
        - 0.01005814 * sil
        - 0.01901894 * arg
        + 0.0001171219 * at * sil
        + 0.0002073924 * at * arg
        + 0.00006118707 * sil * arg
        - 0.000006373789 * at * sil * arg
    )
    return (1 + 0.3591 * x) ** 2.78474 * 10


def classe_ad(ad_mm_cm: float) -> str | None:
    """Classe AD do Art. 2º; None abaixo de 0,34 mm/cm (fora das classes do ZARC)."""
    classe = None
    for nome, limite in LIMITES_AD:
        if ad_mm_cm >= limite:
            classe = nome
    return classe
