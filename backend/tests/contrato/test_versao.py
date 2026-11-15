"""#55 T-026: versão explícita e mudança incompatível."""

import pytest

from tellus.contrato import regras, versao


def test_versao_atual_aceita(pedido_valido):
    assert regras.normalizar_pedido(pedido_valido)["versao_contrato"] == versao.VERSAO


@pytest.mark.parametrize("v,codigo", [("2.0.0", "versao_incompativel"), ("0.9.0", "versao_incompativel"),
                                      ("1.9.0", "versao_incompativel"), ("1.0", "versao_invalida"), (None, "versao_ausente")])
def test_versao_incompativel_informa_aceitas(pedido_valido, v, codigo):
    pedido_valido["versao_contrato"] = v
    with pytest.raises(versao.ErroContrato) as e:
        regras.normalizar_pedido(pedido_valido)
    assert e.value.codigo == codigo
    assert e.value.versoes_aceitas == ["1.0.x", "1.1.x"]
    assert e.value.como_dict()["origem"] == "pedido" and e.value.campo == "versao_contrato"


def test_correcao_mesmo_menor_aceita(pedido_valido):
    pedido_valido["versao_contrato"] = "1.0.7"
    assert regras.normalizar_pedido(pedido_valido)


@pytest.mark.parametrize("v", ["1.0.0", "1.0.7"])
def test_pedido_1_0_sem_campos_novos_permanece_compativel(pedido_valido, v):
    pedido_valido["versao_contrato"] = v
    for premissa in pedido_valido["premissas_editadas"]:
        premissa.pop("origem_informada", None)
        premissa.pop("data_informada", None)
    normalizado = regras.normalizar_pedido(pedido_valido)
    assert normalizado["versao_contrato"] == v
    assert normalizado["premissas_editadas"][0]["origem_informada"] is None
    assert normalizado["premissas_editadas"][0]["data_informada"] is None


def test_resposta_carrega_versao(resposta_real):
    assert resposta_real["versao_contrato"] == versao.VERSAO == resposta_real["versoes"]["contrato"]
