"""#54: a 008 entra na seção do contrato (1.1.0); origem/data informadas; 'não sei'; falha isolada; rota."""

import copy

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.contrato import exemplos, regras, secoes, versao


def _p(**ajuste):
    return regras.normalizar_pedido(copy.deepcopy(exemplos.PEDIDO_VALIDO) | ajuste)


def test_pedido_1_0_continua_aceito():
    p = _p(versao_contrato="1.0.0", premissas_editadas=[
        {"modulo": "economia", "id": "preco_r_saca", "valor_novo": 55.0, "unidade": "R$/saca de 60 kg", "cultura": "sorgo_granifero_2a_safra"}])
    assert p["premissas_editadas"][0]["origem_informada"] is None


def test_origem_e_data_juntas():
    ed = [{"modulo": "economia", "id": "preco_r_saca", "valor_novo": 55.0, "unidade": "R$/saca de 60 kg",
           "cultura": "sorgo_granifero_2a_safra", "origem_informada": "cooperativa"}]
    with pytest.raises(versao.ErroContrato) as e:
        _p(premissas_editadas=ed)
    assert "juntas" in e.value.mensagem


def test_origem_chega_a_proveniencia_da_007():
    r = secoes.calcular(_p())
    sorgo = r["culturas"][1]["economia"]
    prov = next(p for p in sorgo["proveniencia"] if p["id"] == "preco_informado")  # formato do contrato 1.1.0 (Pedro)
    assert prov["periodo"] == "2025-01-15" and "Cooperativa" in prov["fonte"] and prov["situacao"] == "informada_pelo_produtor"
    # a 007 repassa origem e data (não só o contrato a partir do pedido)
    alt = next(a for a in sorgo["conteudo"]["alteracoes"] if a["premissa"] == "preco_r_saca")
    assert alt["origem_informada"] == "Cooperativa local de Rio Verde/GO" and alt["data_informada"] == "2025-01-15"
    assert regras.numeros_sem_proveniencia(r) == []


def test_nao_sei_vai_para_a_recomendacao():
    r = secoes.calcular(_p(grupo="nao_sei"))
    rec = r["recomendacao"]
    assert rec["estado"] == "disponivel"
    assert rec["conteudo"]["grupos_testados"]["sorgo_granifero_2a_safra"] == ["GRUPO I", "GRUPO II", "GRUPO III"]
    for b in r["culturas"]:
        assert b["risco_hidrico"]["obrigatoria"] is False and b["risco_hidrico"]["estado"] == "indisponivel"
    assert regras.numeros_sem_proveniencia(r) == []


def test_cultura_escolhida_mapeia_metodologia():
    r = secoes.calcular(_p(metodologia="cultura_escolhida", cultura="milho_2a_safra"))
    c = r["recomendacao"]["conteudo"]
    assert c["metodologia"] == "cultura_escolhida" and {a["cultura"] for a in c["alternativas"]} == {"milho_2a_safra"}


def test_falha_da_008_nao_derruba_as_outras_secoes():
    def cai(_):
        raise RuntimeError("recomendação fora do ar")
    r = secoes.calcular(_p(), recomendar=cai)
    assert r["recomendacao"]["estado"] == "erro" and r["estado_geral"] == "erro" and r["final"] is False
    assert r["culturas"][0]["risco_hidrico"]["estado"] == "disponivel"
    assert any(e["origem"].startswith("spec 008") for e in r["erros"])


def test_rota_calcular():
    c = TestClient(app)
    r = c.post("/api/contrato/calcular", json=exemplos.PEDIDO_VALIDO)
    assert r.status_code == 200
    j = r.json()
    assert j["versao_contrato"] == "1.2.0" and j["recomendacao"]["estado"] == "disponivel"
    r = c.post("/api/contrato/calcular", json=exemplos.PEDIDO_VALIDO | {"versao_contrato": "2.0.0"})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "versao_incompativel"
