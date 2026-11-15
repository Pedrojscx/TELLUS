"""Estados distintos e auditáveis da consulta CAR (SC-001), sem rede (respostas gravadas)."""

import json
from pathlib import Path

import httpx
import pytest

from tellus.car import servico

FIX = Path(__file__).parent / "fixtures"
COD = "GO-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33"
VAZIO = {"type": "FeatureCollection", "features": [], "numberMatched": 0}


def cliente(resposta=None, status=200, erro=None, texto=None):
    def tratar(req: httpx.Request):
        if erro:
            raise erro
        if texto is not None:
            return httpx.Response(status, text=texto)
        return httpx.Response(status, json=resposta)
    return httpx.Client(transport=httpx.MockTransport(tratar))


def encontrado():
    return json.loads((FIX / "encontrado.json").read_text(encoding="utf-8"))


def test_encontrado(tmp_path):
    r = servico.consultar(COD, tmp_path, cliente(encontrado()))
    assert r["estado"] == "encontrado"
    c = r["candidato"]
    assert c["estado"] == "aguardando_confirmacao"
    assert c["area_ha"] == pytest.approx(35.0, rel=0.01)
    assert c["municipios"][0]["codigo_ibge"] == "5218805"
    assert r["proveniencia"]["fonte"] and r["proveniencia"]["obtido_em"] and r["proveniencia"]["versao"]
    assert r["qualidade"]["condicao"] == "Aguardando análise"
    assert "limite_declarado" in {a["codigo"] for a in r["avisos"]}


def test_inexistente(tmp_path):
    r = servico.consultar(COD, tmp_path, cliente(VAZIO))
    assert r["estado"] == "inexistente" and r["candidato"] is None and r["alternativa"]["upload_sicar"]


def test_codigo_invalido_sem_rede(tmp_path):
    r = servico.consultar("GO-123", tmp_path, cliente(erro=AssertionError("não devia chamar a rede")))
    assert r["estado"] == "codigo_invalido" and r["candidato"] is None


def test_sem_geometria(tmp_path):
    d = encontrado()
    d["features"][0]["geometry"] = None
    r = servico.consultar(COD, tmp_path, cliente(d))
    assert r["estado"] == "sem_geometria" and r["candidato"] is None and r["alternativa"]


def test_geometria_invalida(tmp_path):
    d = encontrado()
    d["features"][0]["geometry"] = {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}
    r = servico.consultar(COD, tmp_path, cliente(d))
    assert r["estado"] == "geometria_invalida" and r["erros_geometria"] and r["candidato"] is None


def test_fonte_fora_do_ar_sem_cache(tmp_path):
    r = servico.consultar(COD, tmp_path, cliente(erro=httpx.ConnectError("caiu")))
    assert r["estado"] == "fonte_indisponivel" and "geoserver.car.gov.br" in r["mensagem"] and r["alternativa"]


def test_fonte_fora_do_ar_usa_cache(tmp_path):
    servico.consultar(COD, tmp_path, cliente(encontrado()))  # grava o cache
    r = servico.consultar(COD, tmp_path, cliente(erro=httpx.ConnectError("caiu")))
    assert r["estado"] == "encontrado"
    assert "cache_usado" in {a["codigo"] for a in r["avisos"]}


def test_xml_de_excecao_vira_fonte_indisponivel(tmp_path):
    r = servico.consultar(COD, tmp_path, cliente(texto="<ows:ExceptionReport/>", status=400))
    assert r["estado"] == "fonte_indisponivel"


def test_estados_todos_distintos(tmp_path):
    estados = {
        servico.consultar(COD, tmp_path / "a", cliente(encontrado()))["estado"],
        servico.consultar(COD, tmp_path / "b", cliente(VAZIO))["estado"],
        servico.consultar("x", tmp_path / "c", cliente(VAZIO))["estado"],
        servico.consultar(COD, tmp_path / "d", cliente(erro=httpx.ConnectError("x")))["estado"],
    }
    assert len(estados) == 4


def test_reprodutivel(tmp_path):
    a = servico.consultar(COD, tmp_path, cliente(encontrado()))
    b = servico.consultar(COD, tmp_path, cliente(encontrado()))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
