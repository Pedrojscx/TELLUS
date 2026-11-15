"""#95/#53: o mesmo cálculo real (contrato 1.1.0 + recomendação 008) com e sem o contexto SMAP.

Usa a série REAL versionada de Rio Verde-GO e o provedor real ligado em app.py (PROVEDORES_CONTEXTO).
Incluir ou remover SMAP não pode mudar recomendação, risco, margem nem estado do resultado.
"""

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.umidade import regras, servico

REF = servico.RAIZ / "referencias" / "umidade"
pytestmark = pytest.mark.skipif(not (REF / "rio_verde_go" / "serie.csv").exists(), reason="série real não versionada")

PEDIDO = {"versao_contrato": "1.1.0",
          "area": {"tipo": "ponto", "lat": -17.785278, "lon": -50.965, "confirmada": True, "codigo_ibge": "5218805"},
          "data_colheita_soja": "2027-01-20", "solo": {"textura": "argilosa"}, "grupo": "nao_sei",
          "metodologia": "comparar_alternativas", "premissas_editadas": [
              {"modulo": "economia", "id": "preco_r_saca", "valor_novo": 55, "unidade": "R$/saca de 60 kg",
               "cultura": "sorgo_granifero_2a_safra", "origem_informada": "Cooperativa local", "data_informada": "2025-01-15"}]}


@pytest.fixture(scope="module")
def respostas():
    mp = pytest.MonkeyPatch()
    mp.setattr(servico, "DIR_REFERENCIA", REF)
    api = TestClient(app)
    com = api.post("/api/contrato/calcular", json=PEDIDO | {"contextos": {"vegetacao": False, "umidade": True}})
    sem = api.post("/api/contrato/calcular", json=PEDIDO | {"contextos": {"vegetacao": False, "umidade": False}})
    mp.undo()
    assert com.status_code == sem.status_code == 200
    return com.json(), sem.json()


def test_smap_presente_de_fato(respostas):
    com, sem = respostas
    assert com["contextos"]["umidade"]["estado"] == "disponivel"
    assert sem["contextos"]["umidade"]["estado"] == "nao_solicitado"


def test_resultado_principal_nao_muda_com_smap(respostas):
    com, sem = respostas
    assert com["recomendacao"]["conteudo"]["alternativas"], "precisa haver recomendação para a comparação valer"
    for k in ("culturas", "recomendacao", "estado_geral", "final", "erros", "premissas_editadas"):
        assert com[k] == sem[k], k
    assert com["versoes"]["hash_principal"] == sem["versoes"]["hash_principal"]


def test_contexto_smap_nao_vira_medicao_previsao_nem_produtividade(respostas):
    u = respostas[0]["contextos"]["umidade"]
    assert u["conteudo"]["natureza"] == "contexto_regional" and u["conteudo"]["opcional"] is True
    assert regras.termos_proibidos(u) == []
    assert not [k for k in regras.chaves(u) if k in regras.CHAVES_PROIBIDAS]
