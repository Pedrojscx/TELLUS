"""ETo contra o Exemplo 18 da FAO-56 (Bruxelas, 6 de julho): resultado publicado 3,9 mm/dia."""

import pytest

from tellus.motor import eto


def test_exemplo_18_fao56():
    # Dados do exemplo: J = 187, Tmax 21,5, Tmin 12,3 °C, ea = 1,409 kPa, u2 = 2,078 m/s, Rs = 22,07 MJ/m²/dia,
    # z = 100 m, latitude 50°48'N. Intermediários publicados: es 1,997; Ra 41,09; Rso 30,90; Rnl 3,71; Rn 13,28.
    r = eto.eto(21.5, 12.3, 22.07, 2.078, 100, 50 + 48 / 60, 187, ea=1.409)
    assert r["es"] == pytest.approx(1.997, abs=0.002)
    assert r["ra"] == pytest.approx(41.09, abs=0.05)
    assert r["rso"] == pytest.approx(30.90, abs=0.05)
    assert r["rnl"] == pytest.approx(3.71, abs=0.02)
    assert r["rn"] == pytest.approx(13.28, abs=0.03)
    assert r["eto"] == pytest.approx(3.9, abs=0.05)


def test_ur_media_ou_ea_obrigatorio():
    with pytest.raises(ValueError):
        eto.eto(30, 18, 20, 2, 700, -17.8, 40)
