"""Chuva por área em Rio Verde-GO com dado REAL (IMERG Final V07B versionado em referencias/clima/rio_verde_go).

Só a célula IMERG (−17,75; −50,95) tem série real guardada. Uma área dentro dela usa dado real.
A geometria de referência do CAR (tests/car/fixtures/encontrado.json) cai noutra célula, sem cache:
o pedido falha com erro que nomeia a célula. Por decisão do usuário (2026-11-15), as células vizinhas
não são baixadas; o caso com várias células é provado com cache sintético (test_area.py).
"""

import json
from pathlib import Path

import pytest

from tellus.car import regras as regras_car
from tellus.clima import servico

REF = servico.DIR_REF / "rio_verde_go" / "serie_diaria.csv"
pytestmark = pytest.mark.skipif(not REF.exists(), reason="série versionada de Rio Verde ausente")

# Quadrado de ≈ 1,1 km em volta da estação A025, inteiro na célula IMERG (−17,75; −50,95)
G_A025 = {"type": "Polygon", "coordinates": [[[-50.97, -17.79], [-50.96, -17.79], [-50.96, -17.78],
                                              [-50.97, -17.78], [-50.97, -17.79]]]}
CAR = Path(__file__).resolve().parents[1] / "car" / "fixtures" / "encontrado.json"


def _id(g):
    return regras_car.id_geometria(g, 6)


def test_area_real_na_celula_da_a025_igual_ao_ponto(tmp_path):
    area = servico.serie(geometria=G_A025, id_geometria=_id(G_A025), inicio="2024-01-01", fim="2024-12-31",
                         dir_cache=tmp_path)
    ponto = servico.serie(-17.785278, -50.965, inicio="2024-01-01", fim="2024-12-31", dir_cache=tmp_path)
    assert area["origem_dados"] == "referencia_versionada"
    loc = area["proveniencia"]["chuva"]["localizacao"]
    assert [(c["chave"], c["peso"]) for c in loc["celulas"]] == [("-17.75_-50.95", 1.0)]
    assert loc["celulas"][0]["obtido_em"] == "2026-11-14"
    assert [d["chuva_mm"] for d in area["dias"]] == [d["chuva_mm"] for d in ponto["dias"]]
    assert len(area["dias"]) == 366
    total = sum(d["chuva_mm"] for d in area["dias"] if d["chuva_mm"] is not None)
    assert total > 0  # chuva real do ano, não zeros


def test_area_real_deterministica(tmp_path):
    a = servico.serie(geometria=G_A025, id_geometria=_id(G_A025), fim="2001-03-31", dir_cache=tmp_path)
    b = servico.serie(geometria=G_A025, id_geometria=_id(G_A025), fim="2001-03-31", dir_cache=tmp_path)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_geometria_do_car_bloqueada_por_celula_sem_cache(tmp_path):
    d = json.loads(CAR.read_text(encoding="utf-8"))
    g = d["features"][0]["geometry"]
    with pytest.raises(servico.ErroClima) as e:
        servico.serie(geometria=g, id_geometria=_id(g), dir_cache=tmp_path)
    assert e.value.codigo == "sem_cache" and "-17.85_-51.05" in e.value.mensagem
