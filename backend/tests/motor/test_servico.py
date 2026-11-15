"""Serviço do motor com dados de Rio Verde (referência versionada): ZARC, versões, sem rede."""

import socket

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.motor import servico

BASE = {"lat": -17.785, "lon": -50.965, "cultura": "milho_2a_safra", "grupo": "GRUPO I", "solo": {"classe": "AD4"}}


@pytest.fixture
def sem_rede(monkeypatch):
    def bloqueado(*a, **k):
        raise OSError("rede bloqueada no teste")
    monkeypatch.setattr(socket, "socket", bloqueado)
    monkeypatch.setattr(socket, "create_connection", bloqueado)


def test_roda_sem_rede_e_e_deterministico(sem_rede):
    a = servico.simular(BASE | {"data_colheita_soja": "02-01"})
    b = servico.simular(BASE | {"data_colheita_soja": "02-01"})
    assert a == b
    assert a["resultado"]["anos_validos"] >= 20


def test_entradas_versionadas():
    r = servico.simular(BASE | {"data_colheita_soja": "02-01"})
    for chave in ("clima", "solo", "cultura", "estado_inicial", "entressafra"):
        assert r["entradas"][chave]["hash"], chave
    assert r["entradas"]["zarc"]["portaria"] == "322"
    assert r["versao_entradas"]
    outra = servico.simular(BASE | {"data_colheita_soja": "02-01", "armazenamento_inicial_frac": 0.5})
    assert outra["versao_entradas"] != r["versao_entradas"]
    assert outra["entradas"]["estado_inicial"]["status"] == "editado"


def test_fora_da_janela_zarc_e_rejeitado():
    with pytest.raises(servico.ErroMotor) as e:
        servico.simular(BASE | {"data_colheita_soja": "03-01"})  # plantio 04/03: decêndio 7, fora para milho G I AD4
    assert e.value.codigo == "fora_da_janela_zarc" and "322" in e.value.mensagem


def test_borda_da_janela():
    # milho G I AD4: decêndio 5 (11 a 20/fev) ainda está na janela (40%); decêndio 6 (21/fev) está fora
    assert servico.simular(BASE | {"data_colheita_soja": "02-10", "data_plantio": "02-20"})["entradas"]["zarc"]["dentro_da_janela"]
    with pytest.raises(servico.ErroMotor):
        servico.simular(BASE | {"data_colheita_soja": "02-10", "data_plantio": "02-21"})


def test_risco_sobe_com_plantio_tardio():
    j = servico.simular_janela(BASE | {"data_colheita_soja": "01-01"})
    riscos = [d["risco_historico_falha_severa"] for d in j["decendios"] if d["situacao"] == "simulado"]
    assert riscos == sorted(riscos) and riscos[-1] > riscos[0]


def test_nao_e_previsao_e_riscos_separados():
    r = servico.simular(BASE | {"data_colheita_soja": "02-01"})
    assert any(a["codigo"] == "nao_e_previsao" for a in r["avisos"])
    assert "distintas" in r["resultado"]["significado_riscos"]
    assert any(a["codigo"] == "hipoteses" for a in r["avisos"])  # Kc/Ky são hipótese e aparecem


def test_pousio_e_palhada_registrados():
    p = servico.simular(BASE | {"data_colheita_soja": "01-20", "data_plantio": "01-30", "entressafra": {"manejo": "pousio"}})
    q = servico.simular(BASE | {"data_colheita_soja": "01-20", "data_plantio": "01-30", "entressafra": {"manejo": "palhada"}})
    assert p["entradas"]["entressafra"]["manejo"] == "pousio" and q["entradas"]["entressafra"]["manejo"] == "palhada"
    assert p["entradas"]["entressafra"]["kc"] > q["entradas"]["entressafra"]["kc"]


def test_api():
    c = TestClient(app)
    r = c.post("/api/motor/simular", json=BASE | {"data_colheita_soja": "02-01"})
    assert r.status_code == 200 and r.json()["resultado"]["risco_zarc_pct"] == 20
    r = c.post("/api/motor/simular", json=BASE | {"data_colheita_soja": "03-01"})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "fora_da_janela_zarc"
    r = c.post("/api/motor/janela", json=BASE | {"cultura": "sorgo_granifero_2a_safra", "solo": {"classe": "3"}, "data_colheita_soja": "01-01"})
    assert r.status_code == 200 and len(r.json()["decendios"]) == 9
