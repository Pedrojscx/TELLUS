"""Cache SINTÉTICO de vegetação para testar sem rede.

Nada aqui é dado real: os valores são uma curva sazonal inventada para exercitar o código, e o
meta.json de cada arquivo leva "sintetico": true, que a resposta repete como aviso.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math

import pytest

from tellus.vegetacao import regras, servico

LAT, LON = -17.785278, -50.965  # Rio Verde-GO (ponto da estação A025, caso de validação)
GRADE = servico.GRADE

# datas com QA ruim (motivo esperado) e uma composição que simplesmente não está no cache
NUVEM_MOD = {"2023-01-17": 3, "2024-02-02": 3, "2023-03-06": 1, "2024-06-25": 2}
AUSENTE_MOD = "2023-07-28"


def ndvi_sintetico(d: dt.date) -> float:
    """Curva inventada: verde no verão chuvoso, seca no inverno."""
    return 0.45 + 0.3 * math.cos(2 * math.pi * (d.timetuple().tm_yday - 30) / 365)


def _gravar(pasta, produto, campos, linhas, pesos):
    pasta.mkdir(parents=True, exist_ok=True)
    p = pasta / f"{produto}.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(campos)
        w.writerows(linhas)
    meta = {
        "produto": produto, "sintetico": True, "obtido_em": "2026-11-15",
        "consulta": "fixture sintética de teste (tests/vegetacao/conftest.py)",
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "pesos": pesos,
    }
    (pasta / f"{produto}.meta.json").write_text(json.dumps(meta, sort_keys=True), encoding="utf-8")


def gravar_modis(pasta, produto: str, pesos: dict[str, float], ruins: dict[str, int], ausente: str | None,
                 pixel_ruim: str | None = None):
    cal = servico.PRODUTOS[produto]["calendario"]
    linhas = []
    for d in regras.calendario(dt.date(2023, 1, 1), dt.date(2024, 12, 31), cal["dia_juliano_inicial"], cal["passo_dias"]):
        if d.isoformat() == ausente:
            continue
        v = ndvi_sintetico(d)
        for px in sorted(pesos):
            rel = ruins.get(d.isoformat(), 0) if (pixel_ruim is None or px == pixel_ruim) else 0
            ndvi = -3000 if rel == -1 else round(v * 10000)
            viq = 2116 | (1 << 8) if rel == 1 else 2116  # marginal com nuvem adjacente (bit 8)
            linhas.append([d.isoformat(), px, ndvi, round(v * 0.6 * 10000), rel, viq])
    _gravar(pasta, produto, ["data", "pixel", "ndvi", "evi", "pixel_reliability", "vi_quality"], linhas, pesos)


def gravar_hls(pasta, pesos: dict[str, float]):
    cenas = [
        ("2024-01-10", "S30", 0),      # válida
        ("2024-01-13", "L30", 2),      # nuvem (bit 1)
        ("2024-01-20", "S30", 8),      # sombra (bit 3)
        ("2024-02-04", "L30", 32),     # água (bit 5): aceita pela hipótese
    ]
    linhas = []
    for d, sensor, fmask in cenas:
        for px in sorted(pesos):
            linhas.append([d, sensor, f"HLS.{sensor}.T22KEV.sintetico", px, 400, 600, 3600, fmask])
    _gravar(pasta, "HLS", ["data", "sensor", "granulo", "pixel", "azul", "vermelho", "nir", "fmask"], linhas, pesos)


@pytest.fixture
def cache_ponto(tmp_path):
    """MOD13Q1 + MYD13Q1 sintéticos no ponto; sem HLS."""
    pasta = tmp_path / servico.chave_ponto(LAT, LON)
    pesos = {regras.pixel_senoidal(LAT, LON, GRADE): 1.0}
    gravar_modis(pasta, "MOD13Q1", pesos, NUVEM_MOD, AUSENTE_MOD)
    gravar_modis(pasta, "MYD13Q1", pesos, {}, None)
    return tmp_path


@pytest.fixture
def cache_ponto_hls(cache_ponto):
    pasta = cache_ponto / servico.chave_ponto(LAT, LON)
    gravar_hls(pasta, {"hls_px_1": 1.0})
    return cache_ponto


# Polígono pequeno (~600 m × 600 m) em Rio Verde, cobrindo alguns pixels de 250 m
POLIGONO = {
    "type": "Polygon",
    "coordinates": [[[-50.968, -17.788], [-50.962, -17.788], [-50.962, -17.782], [-50.968, -17.782], [-50.968, -17.788]]],
}


@pytest.fixture
def cache_poligono(tmp_path):
    from tellus.car import regras as rc

    ident = rc.id_geometria(rc.canonica(POLIGONO, 6), 6)
    pesos = regras.pesos_pixels(rc.canonica(POLIGONO, 6), GRADE)
    um_pixel = sorted(pesos)[0]
    gravar_modis(tmp_path / ident, "MOD13Q1", pesos, {"2023-01-17": 3}, None, pixel_ruim=um_pixel)
    return tmp_path, ident, pesos
