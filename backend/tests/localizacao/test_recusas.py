import pytest

from tellus.localizacao import servico
from tellus.localizacao.referencias import carregar


def _erro(lat, lon):
    with pytest.raises(servico.ErroLocalizacao) as e:
        servico.resolver(carregar(), lat, lon)
    return e.value


def test_nova_york_fora_do_brasil():
    e = _erro(40.71, -74.00)
    assert e.codigo == "fora_do_brasil"
    assert "território brasileiro" in e.mensagem


@pytest.mark.parametrize("lat,lon,campo", [(95, 0, "lat"), ("abc", -50, "lat"), (-17, 200, "lon"), (-17, "nan", "lon")])
def test_coordenada_invalida(lat, lon, campo):
    e = _erro(lat, lon)
    assert (e.codigo, e.campo) == ("coordenada_invalida", campo)


def test_mar_perto_da_costa():
    assert _erro(-23.10, -42.50).codigo == "fora_de_municipio"


def test_fernando_de_noronha_aceito_com_aviso():
    r = servico.resolver(carregar(), -3.85, -32.42)
    assert r["local"]["municipio"]["codigo_ibge"] == "2605459"
    assert "ilha_oceanica" in {a["codigo"] for a in r["avisos"]}
