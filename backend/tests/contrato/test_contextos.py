"""#99 T-068: contextos 009/010 opcionais não alteram o resultado principal.

Os conteúdos abaixo são SINTÉTICOS e opacos para o contrato (formato real fica nas specs 009/010).
"""

import pytest

from tellus.contrato import regras, secoes
from tellus.contrato.modelos import RespostaCalculo

UMIDADE = {"natureza": "contexto_regional", "opcional": True, "itens": [{"valor": 0.27, "estado": "disponivel"}],
           "avisos": [{"codigo": "escala_regional", "mensagem": "Célula de 9 km, não o talhão."}], "dado_sintetico": True}
VEGETACAO = {"natureza": "contexto_historico", "fontes": [], "avisos": [{"codigo": "nao_e_produtividade", "mensagem": "x"}]}
ERRO_VEG = {"erro": {"codigo": "sem_cache", "mensagem": "Sem série MODIS guardada.", "origem": "NASA MODIS MOD13Q1", "campo": None}}


@pytest.fixture(scope="module")
def pedido(request):
    from tellus.contrato import exemplos
    return regras.normalizar_pedido(exemplos.PEDIDO_VALIDO | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra",
                                                             "premissas_editadas": []})


def _com(pedido, veg, umi, respostas):
    p = pedido | {"contextos": {"vegetacao": veg, "umidade": umi}}
    return secoes.calcular(p, respostas)


@pytest.mark.parametrize("veg,umi,respostas,estados", [
    (False, False, {}, ("nao_solicitado", "nao_solicitado")),
    (True, True, {"vegetacao": VEGETACAO, "umidade": UMIDADE}, ("disponivel", "disponivel")),
    (True, True, {"vegetacao": ERRO_VEG, "umidade": UMIDADE}, ("erro", "disponivel")),
    (True, False, {}, ("indisponivel", "nao_solicitado")),
])
def test_principal_igual_com_e_sem_contextos(pedido, veg, umi, respostas, estados):
    base = _com(pedido, False, False, {})
    r = _com(pedido, veg, umi, respostas)
    RespostaCalculo.model_validate(r)
    assert (r["contextos"]["vegetacao"]["estado"], r["contextos"]["umidade"]["estado"]) == estados
    for k in ("culturas", "recomendacao", "estado_geral", "final", "erros"):
        assert r[k] == base[k], k
    assert r["versoes"]["hash_principal"] == base["versoes"]["hash_principal"]


def test_contexto_preserva_avisos_e_conteudo(pedido):
    r = _com(pedido, True, True, {"vegetacao": ERRO_VEG, "umidade": UMIDADE})
    u, v = r["contextos"]["umidade"], r["contextos"]["vegetacao"]
    assert u["conteudo"] == UMIDADE and u["avisos"] == UMIDADE["avisos"]
    assert v["erro"]["origem"] == "NASA MODIS MOD13Q1" and "não depende" in v["erro"]["acao"]
    assert all(a["origem"] != "spec 010 (#52)" for a in r["avisos"])  # avisos do contexto não sobem ao topo
