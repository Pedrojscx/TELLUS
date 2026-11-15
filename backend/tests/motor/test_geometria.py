"""Motor com geometria confirmada (#35): a chuva vem da média ponderada por área (spec 003)."""

from tellus.car import regras as regras_car
from tellus.motor import servico

BASE = {"lat": -17.785, "lon": -50.965, "cultura": "milho_2a_safra", "grupo": "GRUPO I", "solo": {"classe": "AD4"},
        "data_colheita_soja": "02-01"}
# ≈ 1,1 km em volta da A025, inteiro na célula IMERG (−17,75; −50,95), que tem série real versionada
G = {"type": "Polygon", "coordinates": [[[-50.97, -17.79], [-50.96, -17.79], [-50.96, -17.78],
                                         [-50.97, -17.78], [-50.97, -17.79]]]}


def test_simular_com_geometria_usa_a_area_e_dentro_de_uma_celula_iguala_o_ponto():
    ponto = servico.simular(BASE)
    area = servico.simular(BASE | {"geometria": G, "id_geometria": regras_car.id_geometria(G, 6)})
    loc = area["entradas"]["clima"]["proveniencia"]["chuva"]["localizacao"]
    assert loc["tipo"] == "geometria" and [c["peso"] for c in loc["celulas"]] == [1.0]
    assert "tipo" not in ponto["entradas"]["clima"]["proveniencia"]["chuva"]["localizacao"]  # ponto inalterado
    assert area["entradas"]["clima"]["hash"] == ponto["entradas"]["clima"]["hash"]  # mesma série diária
    assert area["resultado"] == ponto["resultado"]
