"""Regras puras do calendário ZARC (Princípio VI)."""

from __future__ import annotations

import calendar
import datetime as dt

# riscos oficiais do ZARC: 20, 30, 40 (% de chance de perda); 0 = fora da janela
CODIGO = {0: "0", 20: "2", 30: "3", 40: "4"}
DECODIFICA = {v: k for k, v in CODIGO.items()}


def decendio(data: dt.date) -> int:
    """Decêndio ZARC (1 a 36): 1 = 1 a 10 de janeiro; o 3º de cada mês vai até o fim do mês."""
    parte = 0 if data.day <= 10 else 1 if data.day <= 20 else 2
    return (data.month - 1) * 3 + parte + 1


def periodo_decendio(n: int, ano: int) -> tuple[dt.date, dt.date]:
    if not 1 <= n <= 36:
        raise ValueError("decêndio deve estar entre 1 e 36")
    mes = (n - 1) // 3 + 1
    parte = (n - 1) % 3
    inicio = dt.date(ano, mes, 1 + 10 * parte)
    fim = dt.date(ano, mes, 10 * (parte + 1)) if parte < 2 else dt.date(ano, mes, calendar.monthrange(ano, mes)[1])
    return inicio, fim


def codificar(riscos: list[int]) -> str:
    if len(riscos) != 36:
        raise ValueError("são 36 decêndios")
    return "".join(CODIGO[r] for r in riscos)


def decodificar(texto: str) -> list[int]:
    return [DECODIFICA[c] for c in texto]


def janela(riscos: list[int]) -> list[dict]:
    """Só os decêndios com risco oficial diferente de zero (FR-004)."""
    return [{"decendio": i + 1, "risco_zarc_pct": r} for i, r in enumerate(riscos) if r]


def consultar(riscos: list[int], data: dt.date) -> dict:
    d = decendio(data)
    r = riscos[d - 1]
    return {"decendio": d, "dentro_da_janela": r > 0, "risco_zarc_pct": r or None}
