"""Simulação histórica: a mesma data de colheita/plantio aplicada a cada ano da série. Puro."""

from __future__ import annotations

import datetime as dt
import statistics
from collections.abc import Sequence

from . import balanco


def _quantis(valores: Sequence[float]) -> dict | None:
    if not valores:
        return None
    v = sorted(valores)
    if len(v) == 1:
        return {str(q): round(v[0], 4) for q in (10, 25, 50, 75, 90)}
    qs = statistics.quantiles(v, n=20, method="inclusive")  # 5%, 10%, ..., 95%
    return {"10": round(qs[1], 4), "25": round(qs[4], 4), "50": round(statistics.median(v), 4),
            "75": round(qs[14], 4), "90": round(qs[17], 4)}


def simular(dias: Sequence[dict], cultura: balanco.Cultura, cad: float, colheita_mmdd: str, plantio_mmdd: str,
            kc_entressafra: float, frac_inicial: float) -> dict:
    """`dias`: [{data: 'AAAA-MM-DD', chuva_mm: float|None, eto_mm: float|None}] em ordem, sem buracos de calendário.

    Cada ano: entressafra de colheita até a véspera do plantio, depois o ciclo inteiro. Qualquer dia sem
    chuva ou ETo dentro dessa janela exclui o ano (série interrompida), com o motivo.
    """
    if not 0 <= frac_inicial <= 1:
        raise ValueError("a fração inicial deve estar entre 0 e 1")
    idx = {d["data"]: i for i, d in enumerate(dias)}
    anos = sorted({d["data"][:4] for d in dias})
    resultados, excluidos = [], []
    for ano in anos:
        try:
            colheita = dt.date.fromisoformat(f"{ano}-{colheita_mmdd}")
            plantio = dt.date.fromisoformat(f"{ano}-{plantio_mmdd}")
        except ValueError:  # 29/02 em ano não bissexto
            excluidos.append({"ano": int(ano), "motivo": "data inexistente neste ano (29/02)"})
            continue
        if plantio < colheita:
            raise ValueError("o plantio não pode ser antes da colheita da soja")
        fim = plantio + dt.timedelta(days=cultura.ciclo - 1)
        i0, i1 = idx.get(colheita.isoformat()), idx.get(fim.isoformat())
        if i0 is None or i1 is None:
            excluidos.append({"ano": int(ano), "motivo": "a série não cobre o período inteiro (colheita até a maturação)"})
            continue
        janela = dias[i0:i1 + 1]
        falta = next((d["data"] for d in janela if d["chuva_mm"] is None or d["eto_mm"] is None), None)
        if falta:
            excluidos.append({"ano": int(ano), "motivo": f"dia climático ausente em {falta}; série interrompida"})
            continue
        n_entre = (plantio - colheita).days
        dr0 = (1 - frac_inicial) * cad
        dr_plantio, _ = balanco.entressafra(dr0, [d["chuva_mm"] for d in janela[:n_entre]],
                                            [d["eto_mm"] for d in janela[:n_entre]], kc_entressafra, cad)
        s = balanco.safra(dr_plantio, [d["chuva_mm"] for d in janela[n_entre:]],
                          [d["eto_mm"] for d in janela[n_entre:]], cultura, cad)
        resultados.append({"ano": int(ano), "plantio": plantio.isoformat(), "maturacao": fim.isoformat(),
                           "agua_no_plantio_frac": round(1 - dr_plantio / cad, 3), **s})
    n = len(resultados)
    falhas = sum(1 for r in resultados if r["falha_severa"])
    perdas = [r["perda_relativa"] for r in resultados if r["perda_relativa"] is not None]
    return {
        "anos_validos": n,
        "anos_excluidos": excluidos,
        "risco_historico": None if n == 0 else round(falhas / n, 4),
        "anos_com_falha": falhas,
        "deficit_mm_mediano": None if n == 0 else round(statistics.median(r["deficit_mm"] for r in resultados), 2),
        "perda_relativa_quantis": _quantis(perdas),
        "por_ano": resultados,
    }
