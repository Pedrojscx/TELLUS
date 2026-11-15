"""Balanço hídrico diário (FAO-56, Kc único, reservatório da zona radicular) e indicadores por safra. Puro.

Convenções (FAO-56, cap. 8):
- Dr = depleção da zona radicular (mm), 0 = capacidade de campo, CAD = ponto de murcha.
- Ks = (CAD - Dr) / ((1 - p)·CAD) quando Dr > p·CAD; senão 1 (eq. 84), calculado com Dr do dia anterior.
- ETa = Ks·Kc·ETo; Dr_i = Dr_{i-1} - P_i + ETa_i, limitada a [0, CAD]; o excedente vira drenagem (eq. 85–88).
- Chuva toda efetiva (sem escoamento superficial): premissa declarada no resultado.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Cultura:
    fases: tuple[int, int, int, int]  # dias das fases I a IV
    kc_ini: float
    kc_med: float
    kc_fim: float
    p: float
    ky_fases: tuple[float, float, float, float] | None  # None = sem resposta de produtividade (cobertura)
    isna_limite_I: float | None
    isna_limite_III: float | None

    @property
    def ciclo(self) -> int:
        return sum(self.fases)


def kc_do_dia(c: Cultura, d: int) -> float:
    """Curva de Kc da FAO-56: constante na fase I, linear na II, constante na III, linear na IV. d = 0..ciclo-1."""
    f1, f2, f3, f4 = c.fases
    if d < f1:
        return c.kc_ini
    if d < f1 + f2:
        return c.kc_ini + (c.kc_med - c.kc_ini) * (d - f1 + 1) / f2
    if d < f1 + f2 + f3:
        return c.kc_med
    return c.kc_med + (c.kc_fim - c.kc_med) * (d - f1 - f2 - f3 + 1) / f4


def fase_do_dia(c: Cultura, d: int) -> int:
    acum = 0
    for i, n in enumerate(c.fases):
        acum += n
        if d < acum:
            return i
    return 3


def passo(dr: float, chuva: float, eto: float, kc: float, cad: float, p: float) -> tuple[float, float, float, float]:
    """Um dia de balanço. Devolve (dr_novo, etc, eta, drenagem)."""
    etc = kc * eto
    raw = p * cad
    ks = 1.0 if dr <= raw else max(0.0, (cad - dr) / ((1 - p) * cad))
    eta = ks * etc
    dr_novo = dr - chuva + eta
    drenagem = 0.0
    if dr_novo < 0:
        drenagem = -dr_novo
        dr_novo = 0.0
    if dr_novo > cad:  # não seca além do ponto de murcha: ETa limitada
        eta -= dr_novo - cad
        dr_novo = cad
    return dr_novo, etc, eta, drenagem


def entressafra(dr0: float, chuva: Sequence[float], eto: Sequence[float], kc: float, cad: float) -> tuple[float, list[dict]]:
    """Intervalo colheita → plantio com Kc constante (pousio ou palhada); p = 1 (evaporação até secar)."""
    dr = dr0
    dias = []
    for p_, e in zip(chuva, eto):
        dr, etc, eta, dren = passo(dr, p_, e, kc, cad, 0.999)
        dias.append({"dr": dr, "etc": etc, "eta": eta, "drenagem": dren})
    return dr, dias


def safra(dr0: float, chuva: Sequence[float], eto: Sequence[float], c: Cultura, cad: float) -> dict:
    """Simula o ciclo inteiro. `chuva` e `eto` têm exatamente c.ciclo dias."""
    if len(chuva) != c.ciclo or len(eto) != c.ciclo:
        raise ValueError("chuva e ETo precisam cobrir o ciclo inteiro")
    dr = dr0
    etc_f = [0.0] * 4
    eta_f = [0.0] * 4
    chuva_f = [0.0] * 4
    drenagem = 0.0
    for d in range(c.ciclo):
        f = fase_do_dia(c, d)
        dr, etc, eta, dren = passo(dr, chuva[d], eto[d], kc_do_dia(c, d), cad, c.p)
        etc_f[f] += etc
        eta_f[f] += eta
        chuva_f[f] += chuva[d]
        drenagem += dren
    isna = [eta_f[i] / etc_f[i] if etc_f[i] > 0 else 1.0 for i in range(4)]
    deficit = [etc_f[i] - eta_f[i] for i in range(4)]
    perda = None
    if c.ky_fases:
        # FAO-33, forma multiplicativa por fase: Ya/Ym = Π (1 - Ky_i·(1 - ETa_i/ETc_i))
        rel = 1.0
        for ky, r in zip(c.ky_fases, isna):
            rel *= max(0.0, 1 - ky * (1 - r))
        perda = 1 - rel
    falha = bool(
        (c.isna_limite_I is not None and isna[0] <= c.isna_limite_I)
        or (c.isna_limite_III is not None and isna[2] <= c.isna_limite_III)
    )
    return {
        "isna_fases": [round(x, 4) for x in isna],
        "deficit_mm_fases": [round(x, 2) for x in deficit],
        "deficit_mm": round(sum(deficit), 2),
        "etc_mm": round(sum(etc_f), 2),
        "eta_mm": round(sum(eta_f), 2),
        "chuva_mm": round(sum(chuva_f), 2),
        "drenagem_mm": round(drenagem, 2),
        "perda_relativa": None if perda is None else round(perda, 4),
        "falha_severa": falha,
        "dr_final": round(dr, 3),
    }
