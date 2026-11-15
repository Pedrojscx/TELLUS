"""Rotas /api/contrato num FastAPI local (o app.py é integrado pelo Maestro)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import contrato


@pytest.fixture
def api():
    app = FastAPI()
    app.include_router(contrato.router)
    return TestClient(app)


def test_versao_com_limites_e_secoes(api):
    j = api.get("/api/contrato/versao").json()
    assert j["versao_contrato"] == "1.0.0" and j["versoes_aceitas"] == ["1.0.x"]
    assert all(v["status"] == "hipotese" for k, v in j["limites"].items() if not k.startswith("_") and k != "vertices_por_anel_max")
    assert j["secoes"]["recomendacao"].startswith("pendente")


def test_esquema(api):
    j = api.get("/api/contrato/esquema").json()
    assert "versao_contrato" in j["pedido"]["properties"] and "culturas" in j["resposta"]["properties"]


def test_validar_pedido(api, pedido_valido):
    r = api.post("/api/contrato/pedido/validar", json=pedido_valido)
    assert r.status_code == 200 and r.json()["valido"] is True and r.json()["pedido"]["hash_pedido"]


@pytest.mark.parametrize("ajuste,codigo,campo", [
    ({"versao_contrato": "2.0.0"}, "versao_incompativel", "versao_contrato"),
    ({"grupo": "IV"}, "pedido_invalido", "grupo"),
    ({"area": {"tipo": "geometria", "id_geometria": "g", "origem": "desenho", "confirmada": True,
               "geometria": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 0]]]}}}, "geometria_invalida", "area.geometria"),
])
def test_erros_no_envelope_unificado(api, pedido_valido, ajuste, codigo, campo):
    r = api.post("/api/contrato/pedido/validar", json=pedido_valido | ajuste)
    assert r.status_code == 422
    e = r.json()["erro"]
    assert {"codigo", "mensagem", "origem", "campo"} <= set(e)
    assert e["codigo"] == codigo and e["campo"] == campo and e["origem"] == "pedido"
    if codigo == "versao_incompativel":
        assert e["versoes_aceitas"] == ["1.0.x"]


def test_corpo_que_nao_e_objeto(api):
    r = api.post("/api/contrato/pedido/validar", json=[1, 2])
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "pedido_invalido"
