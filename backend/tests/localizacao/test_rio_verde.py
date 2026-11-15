"""FR-015 / SC-002: Rio Verde-GO confere com os valores da spec 002 (entrega 1)."""

import pytest

from tellus.localizacao import servico
from tellus.localizacao.referencias import carregar


@pytest.fixture(scope="module")
def resultado():
    return servico.resolver_padrao(carregar())


def _ref(resultado, tipo):
    return next(r for r in resultado["referencias"] if r["tipo"] == tipo)


def test_local_padrao(resultado):
    assert resultado["eh_demo"] is True
    assert resultado["local"]["municipio"] == {"codigo_ibge": "5218805", "nome": "Rio Verde", "uf": "GO"}


def test_estacao_a025(resultado):
    e = _ref(resultado, "estacao_inmet")
    assert e["identificador"] == "A025"
    assert e["detalhes"]["altitude_m"] == pytest.approx(780.11)
    assert e["distancia_km"] < 0.1
    assert e["avisos"] == []


def test_celulas(resultado):
    imerg, power = _ref(resultado, "celula_imerg"), _ref(resultado, "celula_power")
    assert (imerg["lat"], imerg["lon"]) == pytest.approx((-17.75, -50.95), abs=0.01)
    assert (power["lat"], power["lon"]) == pytest.approx((-18.0, -51.25), abs=0.01)


def test_praca_rio_verde(resultado):
    p = _ref(resultado, "praca_conab")
    assert p["nome"] == "Rio Verde-GO"
    for cultura in ("soja", "milho_2a_safra", "sorgo"):
        assert 2026 in p["detalhes"]["culturas"][cultura]
        assert p["detalhes"]["mais_proxima_por_cultura"][cultura]["nome"] == "Rio Verde-GO"
    assert not any(a["codigo"] == "praca_outro_municipio" for a in p["avisos"])


def test_municipio_zarc(resultado):
    assert _ref(resultado, "municipio_zarc")["identificador"] == "5218805"


def test_toda_referencia_tem_procedencia(resultado):
    assert len(resultado["referencias"]) == 5
    for r in resultado["referencias"]:
        proc = r["procedencia"]
        assert proc["fonte"] and proc["url"] and proc["obtido_em"]
        assert proc["status"] in ("fonte", "hipotese")
