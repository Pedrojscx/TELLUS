"""Rotas /api/vegetacao num FastAPI local (o app.py é integrado pelo Maestro)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import vegetacao
from tellus.car import regras as rc
from tellus.vegetacao import servico

from .conftest import LAT, LON, POLIGONO


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    app = FastAPI()
    app.include_router(vegetacao.router)
    return TestClient(app)


def _sem_serie(monkeypatch):
    # o default de dir_series foi fixado na assinatura; o teste isola o repositório explicitamente
    original = servico.contexto
    monkeypatch.setattr(servico, "contexto", lambda **kw: original(dir_series=None, **kw))


def test_get_ponto(cliente, cache_ponto, monkeypatch):
    monkeypatch.setenv("TELLUS_CACHE_VEGETACAO", str(cache_ponto))
    _sem_serie(monkeypatch)
    r = cliente.get("/api/vegetacao/contexto", params={"lat": LAT, "lon": LON})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["finalidade"] == "contexto_historico"
    assert {f["produto"]: f["estado"] for f in corpo["fontes"]} == {"MOD13Q1": "disponivel", "HLS": "indisponivel"}


def test_post_geometria_confirmada(cliente, cache_poligono, monkeypatch):
    cache, ident, _ = cache_poligono
    monkeypatch.setenv("TELLUS_CACHE_VEGETACAO", str(cache))
    _sem_serie(monkeypatch)
    r = cliente.post("/api/vegetacao/contexto", json={"geometria": POLIGONO, "id_geometria": ident,
                                                      "inicio": "2023-01-01", "fim": "2024-12-31"})
    assert r.status_code == 200 and r.json()["area"]["id_geometria"] == ident == rc.id_geometria(POLIGONO, 6)


def test_erros_legiveis(cliente, tmp_path, monkeypatch):
    monkeypatch.setenv("TELLUS_CACHE_VEGETACAO", str(tmp_path))
    _sem_serie(monkeypatch)
    r = cliente.get("/api/vegetacao/contexto", params={"lat": LAT, "lon": LON})
    assert r.status_code == 404
    erro = r.json()["erro"]
    assert erro["codigo"] == "sem_cache" and "MOD13Q1" in erro["origem"]
    r = cliente.get("/api/vegetacao/contexto", params={"lat": "abc", "lon": LON})
    assert r.status_code == 422 and r.json()["erro"]["origem"] == "pedido"
    r = cliente.post("/api/vegetacao/contexto", json={"geometria": POLIGONO, "id_geometria": "x"})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "geometria_nao_confirmada"


def test_token_nao_vaza_na_resposta(cliente, cache_ponto, monkeypatch):
    monkeypatch.setenv("TELLUS_CACHE_VEGETACAO", str(cache_ponto))
    monkeypatch.setenv("EARTHDATA_TOKEN", "segredo-de-teste-123")
    _sem_serie(monkeypatch)
    corpo = cliente.get("/api/vegetacao/contexto", params={"lat": LAT, "lon": LON}).text
    assert "segredo-de-teste-123" not in corpo
