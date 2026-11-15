"""Caso à mão (Princípio VI): média ponderada de 2 células e métricas de 4 dias."""

import pytest

from tellus.clima import regras

A, B = (722, 1290), (722, 1291)
PESOS = {A: 0.25, B: 0.75}


@pytest.mark.parametrize(
    "valores,esperado",
    [
        ({A: 4.0, B: 8.0}, 7.0),  # 0,25·4 + 0,75·8 = 1 + 6 = 7
        ({A: 0.0, B: 2.0}, 1.5),  # 0 + 1,5
        ({A: 10.0, B: None}, None),  # célula ausente: dia ausente, nunca zero
    ],
)
def test_chuva_ponderada_caso_a_mao(valores, esperado):
    assert regras.chuva_ponderada(valores, PESOS) == esperado


def test_metricas_caso_a_mao():
    # ref = [10, 0, 5, 1]; fonte = [8, 2, 5, 0]
    # totais 16 e 15 → viés (15−16)/16 = −6,25%; |dif| = 2,2,0,1 → MAE 1,25; RMSE √(9/4) = 1,5
    # dias ≥ 1 mm: fonte 3/4 = 75%; ref 3/4 = 75%
    m = regras.metricas([10, 0, 5, 1], [8, 2, 5, 0])
    assert m["vies_pct"] == -6.25
    assert m["mae_mm_dia"] == 1.25
    assert m["rmse_mm_dia"] == 1.5
    assert m["frac_dias_chuva_pct"] == 75.0
    assert m["frac_dias_chuva_ref_pct"] == 75.0


def test_ponto_peso_um():
    assert regras.pesos_celulas({"type": "Point", "coordinates": [-50.965, -17.785278]}) == {(722, 1290): 1.0}


def test_poligono_dentro_de_uma_celula():
    quad = {"type": "Polygon", "coordinates": [[[-50.99, -17.79], [-50.96, -17.79], [-50.96, -17.76], [-50.99, -17.76], [-50.99, -17.79]]]}
    assert regras.pesos_celulas(quad) == {(722, 1290): 1.0}


def test_poligono_em_duas_celulas_soma_um():
    # retângulo de -51.02 a -50.98 de longitude: metade em cada célula (borda em -51.0)
    ret = {"type": "Polygon", "coordinates": [[[-51.02, -17.79], [-50.98, -17.79], [-50.98, -17.76], [-51.02, -17.76], [-51.02, -17.79]]]}
    pesos = regras.pesos_celulas(ret)
    assert sum(pesos.values()) == pytest.approx(1.0)
    assert set(pesos) == {(722, 1289), (722, 1290)}
    assert all(w == pytest.approx(0.5, abs=0.05) for w in pesos.values())
