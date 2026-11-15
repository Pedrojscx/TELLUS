"""Série REAL versionada de Rio Verde-GO (MOD13Q1 v061 via ORNL DAAC, obtida em 2026-11-15)."""

import json

import pytest

from tellus.vegetacao import servico

LAT, LON = -17.785278, -50.965
PASTA = servico.DIR_SERIES / servico.chave_ponto(LAT, LON)

pytestmark = pytest.mark.skipif(not (PASTA / "MOD13Q1.csv").exists(), reason="série de Rio Verde não versionada")


def _ctx(tmp_path):
    return servico.contexto(lat=LAT, lon=LON, dir_cache=tmp_path, ambiente={})


def test_rio_verde_ultimos_12_meses_sustenta_minimo(tmp_path):
    r = _ctx(tmp_path)
    mod = r["fontes"][0]
    assert mod["origem"]["tipo"] == "referencia_versionada" and mod["origem"]["sintetico"] is False
    assert mod["area"]["pixels"] == [{"pixel": "h13v10.l3736.c0705", "peso": 1.0}]
    serie = mod["serie"]
    assert (serie[0]["data"], serie[-1]["data"], len(serie)) == ("2025-11-01", "2026-10-16", 23)
    lacunas = {o["data"]: o["qualidade"]["motivo"] for o in serie if o["valor"] is None}
    assert lacunas == {"2025-12-03": "nuvem", "2026-03-06": "possivel_sombra"}
    assert mod["suficiencia"]["estado"] == "suficiente" and mod["suficiencia"]["n_validas"] == 21
    assert r["fontes"][1]["estado"] == "indisponivel"  # HLS sem credencial: não bloqueia
    assert not any(a["codigo"] == "dado_sintetico" for a in r["avisos"])


def test_rio_verde_deterministico(tmp_path):
    assert json.dumps(_ctx(tmp_path), sort_keys=True) == json.dumps(_ctx(tmp_path), sort_keys=True)
