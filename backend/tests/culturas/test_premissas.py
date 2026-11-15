"""Auditoria de fontes (SC-001), hipótese propagada, edição com antes/depois (SC-002), FAO só como método."""

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.culturas import servico

CULTURAS = list(servico.BASE["culturas"])


@pytest.mark.parametrize("cultura", CULTURAS)
def test_todo_parametro_tem_fonte_completa_ou_hipotese(cultura):
    for p in servico.parametros(cultura, "GO")["parametros"]:
        assert p["unidade"], p["id"]
        if p["status"] == "fonte":
            f = p["fonte"]
            assert f and f["documento"] and f["url"] and f["consultado_em"] and f["validade_regional"], p["id"]
            assert p["trecho"], p["id"]
        else:
            assert p["status"] == "hipotese" and p["motivo"], p["id"]


@pytest.mark.parametrize("cultura", CULTURAS)
def test_fao_nunca_e_fonte(cultura):
    for p in servico.parametros(cultura, "GO")["parametros"]:
        if p["metodo_referencia"]:
            assert p["status"] == "hipotese" and p["fonte"] is None, p["id"]
        if p["fonte"]:
            assert "FAO" not in p["fonte"]["id"]


def test_fora_da_validade_regional_vira_hipotese():
    go = {p["id"]: p for p in servico.parametros("milho_2a_safra", "GO")["parametros"]}
    mt = {p["id"]: p for p in servico.parametros("milho_2a_safra", "MT")["parametros"]}
    assert go["cad_mm"]["status"] == "fonte"
    assert mt["cad_mm"]["status"] == "hipotese" and "GO" in mt["cad_mm"]["motivo"]


def test_edicao_preserva_padrao_e_mostra_antes_depois():
    r = servico.premissas("milho_2a_safra", "GO", {"kc.med": 1.10, "ze_cm": 70})
    kc = next(p for p in r["parametros"] if p["id"] == "kc")
    assert kc["valor_padrao"]["med"] == 1.20 and kc["valor_usado"]["med"] == 1.10 and kc["editado"]
    assert {"parametro": "kc.med", "valor_anterior": 1.2, "valor_novo": 1.1, "unidade": "adimensional", "origem_novo": "produtor"} in r["alteracoes"]
    assert servico.parametros("milho_2a_safra", "GO")["parametros"][0]["valor_usado"] == 60  # padrão não foi sobrescrito
    assert kc["status"] == "hipotese"  # a hipótese continua marcada depois da edição


@pytest.mark.parametrize("edicao,codigo", [({"kc.med": 5}, "fora_do_dominio"), ({"ze_cm": -1}, "fora_do_dominio"),
                                           ({"kc": 1.0}, "valor_invalido"), ({"xyz": 1}, "parametro_desconhecido"),
                                           ({"fases_dias.GRUPO I": [20, 30]}, "valor_invalido")])
def test_edicao_invalida(edicao, codigo):
    with pytest.raises(servico.ErroPremissa) as e:
        servico.premissas("milho_2a_safra", "GO", edicao)
    assert e.value.codigo == codigo


def test_solo_por_granulometria_e_fonte_oficial():
    r = servico.classificar_solo("milho_2a_safra", "GO", granulometria={"areia": 60, "silte": 15, "argila": 25})
    assert r["classe"] == "AD4" and r["cad_mm"] == 54.6 and r["status"] == "fonte" and r["origem"] == "granulometria"


def test_solo_por_textura_e_hipotese_com_aviso():
    r = servico.classificar_solo("milho_2a_safra", "GO", textura="arenosa")
    assert r["status"] == "hipotese" and r["aviso"] and r["classe"] in {"AD1", "AD2", "AD3"}


def test_sorgo_textura_oficial():
    r = servico.classificar_solo("sorgo_granifero_2a_safra", "GO", textura="argilosa")
    assert r["classe"] == "3" and r["cad_mm"] == 75.0 and r["status"] == "fonte"


def test_cad_editada_e_abaixo_das_classes():
    r = servico.classificar_solo("milho_2a_safra", "GO", cad_mm=50)
    assert r["status"] == "editado" and r["classe"] == "AD4"
    r = servico.classificar_solo("milho_2a_safra", "GO", cad_mm=15)
    assert r["classe"] is None and r["aviso"]
    with pytest.raises(servico.ErroPremissa):
        servico.classificar_solo("milho_2a_safra", "GO", cad_mm=1000)


def test_braquiaria_toda_hipotese():
    assert all(p["status"] == "hipotese" for p in servico.parametros("braquiaria_cobertura", "GO")["parametros"])


def test_api():
    c = TestClient(app)
    assert set(c.get("/api/culturas").json()["culturas"]) == set(CULTURAS)
    r = c.post("/api/solo/classificar", json={"cultura": "milho_2a_safra", "uf": "GO", "granulometria": {"areia": 60, "silte": 15, "argila": 25}})
    assert r.status_code == 200 and r.json()["classe"] == "AD4"
    r = c.post("/api/culturas/premissas", json={"cultura": "sorgo_granifero_2a_safra", "uf": "GO", "edicoes": {"ky.total": 9}})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "fora_do_dominio"
    assert c.get("/api/culturas/cafe/parametros").status_code == 422
