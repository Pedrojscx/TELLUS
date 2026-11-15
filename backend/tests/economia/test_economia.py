"""Spec 007: composição Conab recomposta, praça + distância, preço CEPEA, edição com antes/depois, margem à mão."""

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.economia import conab, servico

RV = (-17.785, -50.965)
Q = {"10": 0.05, "25": 0.10, "50": 0.20, "75": 0.40, "90": 0.60}


def test_todas_as_planilhas_recompoem():
    for c in ("milho_2a_safra", "sorgo", "soja"):
        for p in servico._conab(c)["planilhas"]:
            assert conab.conferir(p) == [], p["aba"]


def test_itens_recompoem_o_custo_operacional():
    r = servico.margem(*RV, "milho_2a_safra", Q)
    itens = r["custo_conab"]["itens"]
    assert round(sum(i["valor_usado_r_ha"] for i in itens), 2) == r["custo_conab"]["totais_planilha"]["custo_operacional"] == 5889.09
    assert all(i["valor_r_ha"] is not None and i["grupo"] for i in itens)
    assert r["custo_conab"]["mes_referencia"] == "2026-03" and r["custo_conab"]["sistema"] == "PLANTIO DIRETO"


def test_praca_e_distancia_sempre():
    r = servico.margem(-16.6869, -49.2648, "milho_2a_safra", Q)  # Goiânia
    c = r["custo_conab"]
    assert c["praca"] and c["distancia_km"] > 50
    # a praça escolhida tem planilha da mesma cultura
    assert any(p["codigo_ibge"] == c["codigo_ibge"] for p in servico._conab("milho_2a_safra")["planilhas"])


def test_margem_caso_a_mao():
    # milho, central: 6.000 × (1 − 0,20) = 4.800 kg = 80 sc; receita 80 × 67,34 = 5.387,20; custo 5.889,09 → −501,89
    r = servico.margem(*RV, "milho_2a_safra", Q, {"preco_r_saca": 67.34})
    c = r["cenarios"]["central"]
    assert (c["produtividade_kg_ha"], c["sacas_ha"], c["receita_r_ha"], c["margem_r_ha"]) == (4800.0, 80.0, 5387.2, -501.89)
    assert r["cenarios"]["conservador"]["percentil_perda"] == 75 and r["cenarios"]["favoravel"]["percentil_perda"] == 25


def test_preco_cepea_com_metadados():
    p = servico.margem(*RV, "milho_2a_safra", Q)["premissas"]["preco"]
    assert p["status"] == "fonte" and p["unidade"] == "R$/saca de 60 kg"
    assert p["fonte"]["data"] and "Campinas" in p["fonte"]["praca"] and p["fonte"]["url"]


def test_sorgo_sem_preco_nao_tem_margem_factual():
    r = servico.margem(*RV, "sorgo_granifero_2a_safra", Q)
    assert r["margem_disponivel"] is False and all(c["margem_r_ha"] is None for c in r["cenarios"].values())
    assert r["premissas"]["preco"]["status"] == "indisponivel" and "D-005" in r["motivos_indisponivel"][0]


def test_cobertura_sem_custo_e_com_custo():
    r = servico.margem(*RV, "braquiaria_cobertura", None)
    assert r["margem_disponivel"] is False
    r = servico.margem(*RV, "braquiaria_cobertura", None, {"custo_r_ha": 450})
    assert r["margem_disponivel"] and r["cenarios"]["central"]["margem_r_ha"] == -450.0


def test_edicao_mostra_margem_anterior_e_nova():
    r = servico.margem(*RV, "milho_2a_safra", Q, {"preco_r_saca": 80.0, "custo_item.9": 2000.0})
    assert r["estado"] == "com_premissas_do_produtor"
    premissas = {a["premissa"] for a in r["alteracoes"]}
    assert {"preco_r_saca", "custo_item.9"} <= premissas
    comp = r["comparacao"]
    assert comp["margem_anterior_r_ha"]["central"] == -501.89
    # nova: 80 sc × 80 = 6.400; custo 5.889,09 − 2.170,58 + 2.000 = 5.718,51 → 681,49
    assert comp["margem_nova_r_ha"]["central"] == 681.49
    assert r["premissas"]["custo"]["valor_padrao_r_ha"] == 5889.09


def test_nivel_de_custo():
    r = servico.margem(*RV, "milho_2a_safra", Q, {"nivel_custo": "custo_total"})
    assert r["premissas"]["custo"]["valor_usado_r_ha"] == 6886.16


@pytest.mark.parametrize("ed,codigo", [({"preco_r_saca": -1}, "fora_do_dominio"), ({"custo_item.99": 1}, "item_desconhecido"),
                                       ({"nivel_custo": "x"}, "nivel_invalido")])
def test_edicao_invalida(ed, codigo):
    with pytest.raises(servico.ErroEconomia) as e:
        servico.margem(*RV, "milho_2a_safra", Q, ed)
    assert e.value.codigo == codigo


def test_versao_muda_com_premissa():
    a = servico.margem(*RV, "milho_2a_safra", Q)["versao_premissas"]
    b = servico.margem(*RV, "milho_2a_safra", Q, {"preco_r_saca": 70})["versao_premissas"]
    assert a != b


def test_api_com_simulacao():
    c = TestClient(app)
    r = c.post("/api/economia/margem", json={"lat": RV[0], "lon": RV[1], "cultura": "milho_2a_safra",
                                             "simulacao": {"grupo": "GRUPO I", "solo": {"classe": "AD4"}, "data_colheita_soja": "02-01"}})
    assert r.status_code == 200
    j = r.json()
    assert j["margem_disponivel"] and j["versao_entradas_motor"]
    assert c.get("/api/economia/praca", params={"lat": RV[0], "lon": RV[1], "cultura": "sorgo_granifero_2a_safra"}).json()["praca"] == "Rio Verde-GO"
