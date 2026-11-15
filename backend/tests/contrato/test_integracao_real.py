"""Integração 009/010/011 na main: contextos REAIS (série MODIS e SMAP versionadas de Rio Verde) e envelope único de erro."""

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.contrato import exemplos, regras, secoes

cliente = TestClient(app)
PONTO = {"lat": "-17.785278", "lon": "-50.965"}


@pytest.fixture(scope="module")
def pedido():
    return regras.normalizar_pedido(exemplos.PEDIDO_VALIDO | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra",
                                                             "premissas_editadas": []})


def test_contextos_reais_nao_alteram_o_resultado_principal(pedido):
    veg = cliente.get("/api/vegetacao/contexto", params=PONTO)
    umi = cliente.get("/api/umidade/contexto", params={"lat": "-17.785", "lon": "-50.965"})
    assert veg.status_code == 200 and umi.status_code == 200
    assert veg.json().get("finalidade") == "contexto_historico"
    assert umi.json().get("dado_sintetico") is False
    base = secoes.calcular(pedido | {"contextos": {"vegetacao": False, "umidade": False}}, {})
    com = secoes.calcular(pedido | {"contextos": {"vegetacao": True, "umidade": True}},
                          {"vegetacao": veg.json(), "umidade": umi.json()})
    assert com["versoes"]["hash_principal"] == base["versoes"]["hash_principal"]
    assert com["culturas"] == base["culturas"]


@pytest.mark.parametrize("url,params", [
    ("/api/vegetacao/contexto", {"lat": "abc", "lon": "-50"}),
    ("/api/umidade/contexto", {"lat": "abc", "lon": "-50"}),
    ("/api/localizacao", {"lat": "abc", "lon": "-50"}),
])
def test_envelope_unico_de_erro(url, params):
    r = cliente.get(url, params=params)
    assert r.status_code >= 400
    erro = r.json()["erro"]
    assert {"codigo", "mensagem", "origem", "campo"} <= set(erro)
    assert erro["mensagem"]


def test_contrato_registrado_no_app():
    r = cliente.get("/api/contrato/versao")
    assert r.status_code == 200 and r.json()["versao_contrato"].startswith("1.")
