import pytest

from tellus.localizacao import regras

A025 = (-17.785278, -50.965)


def test_celula_power_da_estacao_a025():
    assert regras.celula_power(*A025) == (-18.0, -51.25)


def test_celula_power_do_ponto_antigo_do_registro():
    assert regras.celula_power(-17.80, -50.92) == (-18.0, -50.625)


def test_celula_imerg_da_estacao_a025():
    assert regras.celula_imerg(*A025) == (-17.75, -50.95)


@pytest.mark.parametrize("lat,esperado", [(-17.8, -17.75), (-17.7999, -17.75), (0.0, 0.05), (0.05, 0.05)])
def test_celula_imerg_bordas(lat, esperado):
    assert regras.celula_imerg(lat, 0.0)[0] == esperado


def test_haversine_a025_ao_centro_imerg():
    assert regras.haversine_km(*A025, -17.75, -50.95) == pytest.approx(4.23, abs=0.05)


QUADRADO = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
COM_BURACO = {
    "type": "Polygon",
    "coordinates": [
        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]],
    ],
}


def test_ponto_em_poligono():
    assert regras.ponto_em_poligono(5, 5, QUADRADO)
    assert not regras.ponto_em_poligono(11, 5, QUADRADO)


def test_ponto_no_buraco_fica_fora():
    assert not regras.ponto_em_poligono(5, 5, COM_BURACO)
    assert regras.ponto_em_poligono(2, 2, COM_BURACO)


def test_multipolygon():
    multi = {"type": "MultiPolygon", "coordinates": [QUADRADO["coordinates"], [[[20, 20], [30, 20], [30, 30], [20, 20]]]]}
    assert regras.ponto_em_poligono(22, 28, multi)


def test_mais_proximo_desempata_pelo_identificador():
    itens = [{"id": "B", "p": (0, 1)}, {"id": "A", "p": (0, -1)}]
    item, d = regras.mais_proximo(0, 0, itens, lambda i: i["p"], lambda i: i["id"])
    assert item["id"] == "A"
