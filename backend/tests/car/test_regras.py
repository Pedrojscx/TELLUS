"""Casos à mão das regras de geometria (Princípio VI)."""

import json
from pathlib import Path

import pytest

from tellus.car import regras

FIX = Path(__file__).parent / "fixtures"


def quadrado(lon0, lat0, lado):
    return {"type": "Polygon", "coordinates": [[[lon0, lat0], [lon0 + lado, lat0], [lon0 + lado, lat0 + lado], [lon0, lat0 + lado], [lon0, lat0]]]}


def test_area_quadrado_no_equador():
    # lado = 6.371.008,8 m × 0,01° × π/180 = 1.111,95 m; área = 1.236.433 m² = 123,64 ha
    assert regras.area_ha(quadrado(-0.005, -0.005, 0.01)) == pytest.approx(123.64, abs=0.05)


def test_area_imovel_car_confere_com_declarada():
    geom = json.loads((FIX / "encontrado.json").read_text(encoding="utf-8"))["features"][0]
    # o CAR declara 35,0003 ha; o cálculo deve ficar a menos de 1%
    assert regras.area_ha(geom["geometry"]) == pytest.approx(geom["properties"]["area"], rel=0.01)


def test_buraco_desconta_area():
    g = quadrado(0, 0, 0.02)
    g["coordinates"].append([[0.005, 0.005], [0.005, 0.015], [0.015, 0.015], [0.015, 0.005], [0.005, 0.005]])
    assert regras.area_ha(g) == pytest.approx(regras.area_ha(quadrado(0, 0, 0.02)) * 0.75, rel=0.001)


def test_valido():
    assert regras.validar_poligono(quadrado(-51, -17.9, 0.01)) == []


def test_laco_em_oito():
    oito = {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}
    assert any("cruza" in m for m in regras.validar_poligono(oito))


def test_anel_aberto_e_curto():
    aberto = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]}
    assert any("não fechado" in m for m in regras.validar_poligono(aberto))
    curto = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]}
    assert any("menos de 4" in m for m in regras.validar_poligono(curto))


def test_coordenada_projetada_recusada():
    utm = quadrado(500000, 8000000, 1000)
    assert any("fora da faixa" in m for m in regras.validar_poligono(utm))


def test_vertices_demais():
    import math
    n = 50
    anel = [[math.cos(2 * math.pi * i / n) * 0.01, math.sin(2 * math.pi * i / n) * 0.01] for i in range(n)]
    anel.append(anel[0])
    g = {"type": "Polygon", "coordinates": [anel]}
    assert regras.validar_poligono(g, max_vertices=1000) == []
    assert any("vértices" in m for m in regras.validar_poligono(g, max_vertices=20))


@pytest.mark.parametrize(
    "entrada,saida",
    [
        ("go-5218805-8f8b1082570b4c1799adbee6ce0eee33", "GO-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33"),
        (" GO-5218805-8F8B.1082.570B.4C17.99AD.BEE6.CE0E.EE33 ", "GO-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33"),
        ("GO-5218805-8F8B", None),
        ("XX-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33", None),
        ("", None),
    ],
)
def test_normalizar_codigo(entrada, saida):
    assert regras.normalizar_codigo(entrada) == saida


def test_id_estavel_com_arredondamento():
    a = quadrado(-51.0, -17.9, 0.01)
    b = quadrado(-51.0000000001, -17.9, 0.01)
    assert regras.id_geometria(a) == regras.id_geometria(b)
