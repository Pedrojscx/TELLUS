from fastapi.testclient import TestClient

from tellus.api.app import app

cliente = TestClient(app)


def test_busca_rio_verde():
    r = cliente.get("/api/municipios", params={"busca": "rio verde"})
    assert r.status_code == 200
    codigos = {m["codigo_ibge"] for m in r.json()["resultados"]}
    assert {"5218805", "5007406"} <= codigos


def test_busca_sem_acento():
    r = cliente.get("/api/municipios", params={"busca": "goiania"})
    assert ("Goiânia", "GO") in {(m["nome"], m["uf"]) for m in r.json()["resultados"]}


def test_busca_curta_demais():
    r = cliente.get("/api/municipios", params={"busca": "r"})
    assert r.status_code == 422
    assert r.json()["erro"]["campo"] == "busca"


def test_padrao():
    r = cliente.get("/api/localizacao/padrao")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["eh_demo"] is True
    assert [x["tipo"] for x in corpo["referencias"]] == [
        "celula_power", "celula_imerg", "estacao_inmet", "praca_conab", "municipio_zarc",
    ]


def test_municipio_por_codigo():
    r = cliente.get("/api/localizacao/municipio/5208707")  # Goiânia
    assert r.status_code == 200
    assert r.json()["local"]["meio"] == "busca"


def test_municipio_inexistente():
    r = cliente.get("/api/localizacao/municipio/9999999")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "municipio_nao_encontrado"


def test_ponto_fora_do_brasil():
    r = cliente.get("/api/localizacao", params={"lat": 40.71, "lon": -74.0})
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "fora_do_brasil"


def test_ponto_por_mapa():
    r = cliente.get("/api/localizacao", params={"lat": -17.785, "lon": -50.965, "meio": "mapa"})
    assert r.status_code == 200
    assert r.json()["local"]["municipio"]["codigo_ibge"] == "5218805"
