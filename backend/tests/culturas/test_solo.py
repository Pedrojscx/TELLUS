"""Equação oficial de AD (IN SPA/MAPA nº 1/2022) e classes — casos à mão."""

import pytest

from tellus.culturas import solo


def test_equacao_caso_a_mao():
    # AT=60, SIL=15, ARG=25:
    # x = -0,02128887·60 - 0,01005814·15 - 0,01901894·25 + 0,0001171219·900 + 0,0002073924·1500
    #     + 0,00006118707·375 - 0,000006373789·22500
    #   = -1,2773322 - 0,1508721 - 0,4754735 + 0,1054097 + 0,3110886 + 0,0229452 - 0,1434103 = -1,6076446
    # AD = (1 + 0,3591·x)^2,78474 · 10 = (0,4226948)^2,78474 · 10 ≈ 0,909 mm/cm
    assert solo.agua_disponivel_mm_cm(60, 15, 25) == pytest.approx(0.909, abs=0.001)


@pytest.mark.parametrize("ad,classe", [(0.33, None), (0.34, "AD1"), (0.459, "AD1"), (0.46, "AD2"), (0.80, "AD4"),
                                       (1.059, "AD4"), (1.40, "AD6"), (2.0, "AD6")])
def test_limites_das_classes(ad, classe):
    assert solo.classe_ad(ad) == classe


def test_classes_vezes_ze_dao_cad_da_portaria_322():
    # Portaria 322 (Ze 60 cm): 24; 31,8; 41,4; 54,6; 72,6; 95,4 mm → 0,40; 0,53; 0,69; 0,91; 1,21; 1,59 mm/cm
    for mm, classe in [(24, "AD1"), (31.8, "AD2"), (41.4, "AD3"), (54.6, "AD4"), (72.6, "AD5"), (95.4, "AD6")]:
        assert solo.classe_ad(mm / 60) == classe


@pytest.mark.parametrize("g", [(-1, 50, 51), (50, 50, 50), (101, 0, 0), ("a", 0, 0)])
def test_granulometria_invalida(g):
    with pytest.raises(ValueError):
        solo.agua_disponivel_mm_cm(*g)
