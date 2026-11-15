"""Spec 008: paridade das metodologias, ZARC em 100%, 'não sei', ausência de recomendação, ordem declarada."""

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.recomendacao import servico
from tellus.zarc import servico as zarc

BASE = {"lat": -17.785, "lon": -50.965, "solo": {"textura": "argilosa"}, "data_colheita_soja": "01-20"}
ECO = {"sorgo_granifero_2a_safra": {"preco_r_saca": 50}, "braquiaria_cobertura": {"custo_r_ha": 400}}


@pytest.fixture(scope="module")
def completo():
    return servico.recomendar(BASE | {"metodologia": "calculo_completo", "edicoes_economia": ECO})


@pytest.fixture(scope="module")
def milho():
    return servico.recomendar(BASE | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra", "edicoes_economia": ECO})


def _por_chave(alts):
    campos = ("risco_zarc_pct", "risco_historico_falha_severa", "deficit_mm_mediano", "perda_relativa_quantis", "margem_r_ha", "versoes", "data_plantio")
    return {(a["cultura"], a["grupo"], a["decendio"]): {c: a[c] for c in campos} for a in alts}


def test_paridade_entre_metodologias(completo, milho):
    m = _por_chave(milho["alternativas"])
    c = {k: v for k, v in _por_chave(completo["alternativas"]).items() if k[0] == "milho_2a_safra"}
    assert m and m == c


def test_todas_dentro_do_zarc(completo):
    cz = {"milho_2a_safra": "milho_2a_safra", "sorgo_granifero_2a_safra": "sorgo_granifero_2a_safra", "braquiaria_cobertura": "milho_2a_safra_braquiaria"}
    for a in completo["alternativas"]:
        solo = "3" if a["cultura"].startswith("sorgo") else None
        r = zarc.consultar_data("5218805", cz[a["cultura"]], f"2027-{a['data_plantio']}", a["grupo"], solo)
        assert any(x["dentro_da_janela"] for x in r["resultados"]), a


def test_nao_sei_mostra_todos_os_grupos(completo):
    assert completo["grupo_informado"] is None
    assert completo["grupos_testados"]["sorgo_granifero_2a_safra"] == ["GRUPO I", "GRUPO II", "GRUPO III"]
    grupos_sorgo = {a["grupo"] for a in completo["alternativas"] if a["cultura"].startswith("sorgo")}
    assert grupos_sorgo == {"GRUPO I", "GRUPO II", "GRUPO III"}


def test_ordem_segue_criterio_declarado(completo):
    alts = completo["alternativas"]
    chaves = [(-a["margem_r_ha"]["conservador"], a["risco_historico_falha_severa"], a["risco_zarc_pct"], a["decendio"]) for a in alts]
    assert chaves == sorted(chaves)
    assert [c["campo"] for c in completo["criterio_ordem"]][0] == "margem_r_ha.conservador"
    assert completo["recomendada"] == alts[0] and alts[0]["posicao"] == 1


def test_riscos_e_margem_separados(completo):
    a = completo["alternativas"][0]
    assert {"risco_zarc_pct", "risco_historico_falha_severa", "margem_r_ha"} <= set(a)
    assert a["versoes"]["motor"] and a["versoes"]["economia"]
    codigos = {x["codigo"] for x in completo["avisos"]}
    assert {"nao_e_previsao", "riscos_distintos", "percentis"} <= codigos


def test_sem_dados_completos_nao_recomenda():
    r = servico.recomendar(BASE | {"metodologia": "cultura_escolhida", "cultura": "sorgo_granifero_2a_safra"})  # sem preço
    assert r["recomendada"] is None and r["alternativas"] == []
    assert any(a["codigo"] == "sem_recomendacao" for a in r["avisos"])
    assert r["indisponiveis"] and "D-005" in r["indisponiveis"][-1]["motivo"]


def test_completo_sem_edicoes_recomenda_so_o_que_tem_dados():
    r = servico.recomendar(BASE | {"metodologia": "calculo_completo"})
    assert {a["cultura"] for a in r["alternativas"]} == {"milho_2a_safra"}
    assert {i["cultura"] for i in r["indisponiveis"]} >= {"sorgo_granifero_2a_safra", "braquiaria_cobertura"}


def test_cad_informada_sem_classe_zarc_so_tira_a_cultura():
    """#102: CAD editada pelo produtor; sorgo (classe por tipo de solo) fica indisponível, milho segue."""
    r = servico.recomendar(BASE | {"solo": {"cad_mm": 72}, "metodologia": "calculo_completo", "edicoes_economia": ECO})
    assert "milho_2a_safra" in {a["cultura"] for a in r["alternativas"]}
    assert any(i["cultura"] == "sorgo_granifero_2a_safra" and "classe do ZARC" in i["motivo"] for i in r["indisponiveis"])


def test_grupo_informado_limita():
    r = servico.recomendar(BASE | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra", "grupo": "GRUPO II"})
    assert {a["grupo"] for a in r["alternativas"]} == {"GRUPO II"}


def test_erros():
    with pytest.raises(servico.ErroRecomendacao):
        servico.recomendar(BASE | {"metodologia": "cultura_escolhida"})
    with pytest.raises(servico.ErroRecomendacao):
        servico.recomendar(BASE | {"metodologia": "x"})


def test_api():
    r = TestClient(app).post("/api/recomendacao", json=BASE | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra"})
    assert r.status_code == 200 and r.json()["recomendada"]["cultura"] == "milho_2a_safra"
