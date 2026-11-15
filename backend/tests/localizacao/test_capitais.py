"""SC-003: 10 capitais + Rio Verde-GO resolvem para o município certo."""

import pytest

from tellus.localizacao import servico
from tellus.localizacao.referencias import carregar

PONTOS = [
    ("Brasília", "DF", -15.7939, -47.8828),
    ("Goiânia", "GO", -16.6869, -49.2648),
    ("Cuiabá", "MT", -15.6014, -56.0979),
    ("Campo Grande", "MS", -20.4697, -54.6201),
    ("São Paulo", "SP", -23.5505, -46.6333),
    ("Belo Horizonte", "MG", -19.9167, -43.9345),
    ("Salvador", "BA", -12.9714, -38.5014),
    ("Manaus", "AM", -3.1190, -60.0217),
    ("Porto Alegre", "RS", -30.0346, -51.2177),
    ("Palmas", "TO", -10.1844, -48.3336),
    ("Rio Verde", "GO", -17.785278, -50.965),
]


@pytest.mark.parametrize("nome,uf,lat,lon", PONTOS)
def test_municipio_certo(nome, uf, lat, lon):
    m, _ = servico.municipio_do_ponto(carregar(), lat, lon)
    assert (m["nome"], m["uf"]) == (nome, uf)
