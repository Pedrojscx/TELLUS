"""Rotas /api/umidade num FastAPI local (o app.py é integrado pelo Maestro)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import umidade as rota
from tellus.umidade import servico

from .conftest import LAT, LON


@pytest.fixture
def api(cache_sintetico, monkeypatch):
    monkeypatch.setattr(servico, "DIR_CACHE", cache_sintetico)
    app = FastAPI()
    app.include_router(rota.router)
    return TestClient(app)


def test_get_contexto(api):
    r = api.get("/api/umidade/contexto", params={"lat": LAT, "lon": LON})
    assert r.status_code == 200
    j = r.json()
    assert j["natureza"] == "contexto_regional" and j["regra_periodo"]["contagem"]["observacoes_validas"] == 3
    assert all(i["aviso_escala"]["espacial"] for i in j["itens"])


def test_post_geometria(api):
    poly = {"type": "Polygon", "coordinates": [[[LON, LAT], [LON + 0.005, LAT], [LON + 0.005, LAT + 0.005], [LON, LAT]]]}
    r = api.post("/api/umidade/contexto", json={"geometria": poly, "data": "2025-01-10"})
    assert r.status_code == 200 and r.json()["itens"][0]["valor"] == 0.3124


def test_erros_legiveis(api, tmp_path, monkeypatch):
    assert api.get("/api/umidade/contexto", params={"lat": "x", "lon": LON}).json()["erro"]["codigo"] == "coordenada_invalida"
    assert api.post("/api/umidade/contexto", json={"geometria": {"type": "Line"}}).status_code == 422
    monkeypatch.setattr(servico, "DIR_CACHE", tmp_path / "vazio")
    r = api.get("/api/umidade/contexto", params={"lat": LAT, "lon": LON})
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "sem_cache" and "SMAP" in r.json()["erro"]["origem"]


def test_produtos(api):
    j = api.get("/api/umidade/produtos").json()
    assert j["hipotese_em_uso"] == "SPL3SMP_E" and j["decisao"]["estado"] == "decisao_pendente"
