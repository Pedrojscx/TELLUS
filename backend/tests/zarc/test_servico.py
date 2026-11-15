from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.zarc import servico

RV = "5218805"


def test_nao_sei_separa_grupos():
    cal = servico.calendario(RV, "sorgo_granifero_2a_safra")
    assert [g["grupo"] for g in cal["grupos"]] == ["GRUPO I", "GRUPO II", "GRUPO III"]
    assert cal["grupo_informado"] is None


def test_so_decendios_com_risco():
    cal = servico.calendario(RV, "milho_2a_safra", "GRUPO I", "AD4")
    assert all(j["risco_zarc_pct"] in (20, 30, 40) for j in cal["grupos"][0]["solos"][0]["janela"])


def test_consulta_dentro_e_fora():
    dentro = servico.consultar_data(RV, "milho_2a_safra", "2027-01-15", "GRUPO I", "AD4")["resultados"][0]
    fora = servico.consultar_data(RV, "milho_2a_safra", "2027-03-15", "GRUPO I", "AD4")["resultados"][0]
    assert dentro == dentro | {"decendio": 2, "dentro_da_janela": True, "risco_zarc_pct": 20}
    assert fora["dentro_da_janela"] is False and fora["risco_zarc_pct"] is None


def test_bloqueio_fora_da_janela():
    assert servico.permitido(RV, "milho_2a_safra", "2027-01-05", "GRUPO I", "AD1")
    assert not servico.permitido(RV, "milho_2a_safra", "2027-03-01", "GRUPO I", "AD1")


def test_uf_nao_baixada_nao_infere(monkeypatch):
    # as 27 UFs estão baixadas; simula uma UF sem arquivo
    monkeypatch.setattr(servico, "_uf", lambda safra, uf: None)
    cal = servico.calendario("4314902", "milho_2a_safra")  # Porto Alegre-RS
    assert cal["disponivel"] is False and "RS" in cal["motivo"] and cal["grupos"] == []


def test_uf_sem_zarc_da_cultura_declara_lacuna():
    cal = servico.calendario("4314902", "milho_2a_safra")  # RS não tem milho 2ª safra zoneado
    assert cal["disponivel"] is False and "vizinho" in cal["motivo"]


def test_combinacao_ausente_nao_infere(monkeypatch):
    # em GO todos os municípios têm sorgo; simula Rio Verde sem a cultura (vizinhos continuam com ela)
    import copy
    dados = copy.deepcopy(servico._uf(servico.SAFRA, "GO"))
    del dados["municipios"][RV]["sorgo_granifero_2a_safra"]
    monkeypatch.setattr(servico, "_uf", lambda safra, uf: dados)
    cal = servico.calendario(RV, "sorgo_granifero_2a_safra")
    assert cal["disponivel"] is False and "vizinho" in cal["motivo"]


def test_risco_zarc_separado_do_historico():
    cal = servico.calendario(RV, "milho_2a_safra", "GRUPO I", "AD4")
    assert "não é o risco histórico" in cal["significado"].lower()
    j = cal["grupos"][0]["solos"][0]["janela"][0]
    assert set(j) == {"decendio", "risco_zarc_pct"}


def test_api():
    c = TestClient(app)
    r = c.get("/api/zarc/calendario", params={"codigo_ibge": RV, "cultura": "milho_2a_safra", "grupo": "GRUPO I", "solo": "AD6"})
    assert r.status_code == 200 and r.json()["grupos"][0]["proveniencia"]["portaria"] == "322"
    r = c.get("/api/zarc/consulta", params={"codigo_ibge": RV, "cultura": "soja", "data": "2026-10-15"})
    assert r.status_code == 200 and all(x["dentro_da_janela"] for x in r.json()["resultados"])
    assert c.get("/api/zarc/calendario", params={"codigo_ibge": RV, "cultura": "cafe"}).status_code == 422
