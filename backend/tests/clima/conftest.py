"""Cache falso e pequeno para testar o serviço sem rede."""

import csv
import json

import pytest

from tellus.clima import imerg, power

LAT, LON = -17.785278, -50.965


@pytest.fixture
def cache_falso(tmp_path):
    cel = imerg.CelulaImerg.do_ponto(LAT, LON)
    p = imerg.arquivo_cache(tmp_path, cel)
    p.parent.mkdir(parents=True)
    linhas = [
        ("2025-09-28", "3.5000", "48", "ok"),
        ("2025-09-29", "", "0", "sem_dado"),
        ("2025-09-30", "0.0000", "48", "ok"),
        ("2025-10-01", "", "", "nao_publicado"),
    ]
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(imerg.CAMPOS)
        for d, v, c, s in linhas:
            w.writerow([d, v, c, s, "2026-11-14"])
    pp = power.arquivo_cache(tmp_path, LAT, LON)
    pp.parent.mkdir(parents=True)
    dias = ["20250928", "20250929", "20250930", "20251001"]
    serie = lambda v: {d: v for d in dias}  # noqa: E731
    bruto = {
        "geometry": {"type": "Point", "coordinates": [-51.25, -18.0, 731.58]},
        "properties": {"parameter": {
            "T2M_MAX": serie(30.0), "T2M_MIN": serie(18.0), "ALLSKY_SFC_SW_DWN": serie(20.0) | {"20250929": -999.0},
            "RH2M": serie(60.0), "WS2M": serie(2.0), "PRECTOTCORR": serie(99.0),
        }},
        "header": {"fill_value": -999.0, "sources": ["MERRA2", "SYN1DEG", "POWER"]},
        "parameters": {},
    }
    pp.write_text(json.dumps(bruto), encoding="utf-8")
    pp.with_suffix(".json.meta.json").write_text(json.dumps({"url": "https://power", "obtido_em": "2026-11-14"}), encoding="utf-8")
    return tmp_path
