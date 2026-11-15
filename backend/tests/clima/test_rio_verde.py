"""SC-002: Rio Verde-GO reproduz a comparação da pesquisa de chuva (1.218 dias, jan–jun).

Usa o IMERG baixado de novo pelo cliente (cache ou referência versionada) e a série da estação
A025 validada na pesquisa: confere o cliente de ponta a ponta.
"""

import pytest

from tellus.clima import servico


@pytest.fixture(scope="module")
def validacao():
    try:
        return servico.validacao(-17.785278, -50.965, "jan-jun")
    except servico.ErroClima as e:
        pytest.skip(f"sem dados de clima de Rio Verde: {e.mensagem}")


def test_dias_pareados(validacao):
    assert validacao["disponivel"] is True
    assert validacao["dias_pareados"] == 1218


def test_imerg_contra_a025(validacao):
    m = validacao["metricas"]["imerg"]
    assert m["vies_pct"] == pytest.approx(-1.03, abs=0.05)
    assert m["mae_mm_dia"] == pytest.approx(4.13, abs=0.02)
    assert m["total_ref_mm"] == pytest.approx(6349.6, abs=0.1)
    assert m["total_mm"] == pytest.approx(6284.47, abs=0.5)


def test_power_contra_a025(validacao):
    assert validacao["metricas"]["power_chuva"]["vies_pct"] == pytest.approx(-26.96, abs=0.05)


def test_outra_estacao_indisponivel():
    v = servico.validacao(-16.6869, -49.2648)  # Goiânia
    assert v["disponivel"] is False and v["motivo"]
