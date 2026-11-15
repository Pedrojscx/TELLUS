import datetime as dt

import pytest

from tellus.zarc import regras


@pytest.mark.parametrize(
    "data,esperado",
    [
        ("2026-01-01", 1), ("2026-01-10", 1), ("2026-01-11", 2), ("2026-01-20", 2), ("2026-01-21", 3), ("2026-01-31", 3),
        ("2026-02-21", 6), ("2026-02-28", 6), ("2028-02-29", 6), ("2026-03-21", 9), ("2026-12-21", 36), ("2026-12-31", 36),
    ],
)
def test_decendio(data, esperado):
    assert regras.decendio(dt.date.fromisoformat(data)) == esperado


def test_todos_os_dias_do_ano_bissexto():
    d = dt.date(2028, 1, 1)
    vistos = []
    while d.year == 2028:
        n = regras.decendio(d)
        ini, fim = regras.periodo_decendio(n, 2028)
        assert ini <= d <= fim
        vistos.append(n)
        d += dt.timedelta(days=1)
    assert sorted(set(vistos)) == list(range(1, 37))


def test_codificar_e_janela():
    riscos = [20, 20, 20, 40] + [0] * 32
    assert regras.decodificar(regras.codificar(riscos)) == riscos
    assert regras.janela(riscos) == [
        {"decendio": 1, "risco_zarc_pct": 20}, {"decendio": 2, "risco_zarc_pct": 20},
        {"decendio": 3, "risco_zarc_pct": 20}, {"decendio": 4, "risco_zarc_pct": 40},
    ]
    assert regras.consultar(riscos, dt.date(2027, 2, 15)) == {"decendio": 5, "dentro_da_janela": False, "risco_zarc_pct": None}
