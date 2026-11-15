"""SC-001: exemplos gravados válidos e de erro passam na validação da versão; esquemas e determinismo."""

import json
from pathlib import Path

import pytest

from tellus.contrato import exemplos, regras, secoes, versao
from tellus.contrato.modelos import PedidoCalculo, RespostaCalculo

CONTRATOS = Path(__file__).resolve().parents[3] / "specs" / "011-contrato-api" / "contracts"


def _ler(nome):
    return json.loads((CONTRATOS / nome).read_text(encoding="utf-8"))


def test_pedido_valido_gravado():
    assert regras.normalizar_pedido(_ler("exemplos/pedido_valido.json"))


@pytest.mark.parametrize("nome", sorted(exemplos.EXEMPLOS_ERRO))
def test_exemplos_de_erro_falham_com_o_codigo_esperado(nome):
    ex = _ler(f"exemplos/{nome}")
    with pytest.raises(versao.ErroContrato) as e:
        regras.normalizar_pedido(ex["pedido"])
    assert e.value.codigo == ex["erro_esperado"]


def test_resposta_gravada_valida_e_rastreavel():
    r = _ler("exemplos/resposta_rio_verde.json")
    RespostaCalculo.model_validate(r)
    assert r["versao_contrato"] == versao.VERSAO
    assert regras.numeros_sem_proveniencia(r) == []


def test_esquemas_gravados_iguais_aos_modelos():
    assert _ler("pedido.schema.json") == json.loads(json.dumps(PedidoCalculo.model_json_schema()))
    assert _ler("resposta.schema.json") == json.loads(json.dumps(RespostaCalculo.model_json_schema()))


def test_determinismo_resposta_gravada_igual_a_recalculada(resposta_real):
    gravada = _ler("exemplos/resposta_rio_verde.json")
    assert json.loads(json.dumps(resposta_real, sort_keys=True)) == gravada


def test_determinismo_duas_execucoes(pedido_valido):
    p = regras.normalizar_pedido(pedido_valido | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra", "premissas_editadas": []})
    a, b = secoes.calcular(p), secoes.calcular(p)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
