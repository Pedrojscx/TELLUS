"""#98 T-067: resultado, aviso e erro distinguíveis; cache com data; sem cache, erro com origem."""

from tellus.clima.servico import ErroClima
from tellus.contrato import regras, secoes
from tellus.contrato.modelos import RespostaCalculo


def _pedido(pedido_valido):
    return regras.normalizar_pedido(pedido_valido | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra",
                                                     "premissas_editadas": []})


def test_estruturas_distintas(resposta_real):
    assert all(a["tipo"] == "aviso" for a in resposta_real["avisos"])
    assert {s["estado"] for b in resposta_real["culturas"] for s in (b["risco_hidrico"], b["economia"])} <= {"disponivel", "indisponivel"}
    assert resposta_real["erros"] == []


def test_cache_aparece_com_data(resposta_real):
    """A série de Rio Verde vem da referência versionada (cópia guardada): estado cache, com data."""
    imerg = [f for f in resposta_real["fontes"] if "IMERG" in f["fonte"]]
    assert imerg and all(f["estado"] == "cache" and f["obtido_em"] for f in imerg)
    av = {a["codigo"]: a["mensagem"] for a in resposta_real["avisos"]}
    assert "cache_usado" in av and imerg[0]["obtido_em"] in av["cache_usado"]


def test_fonte_sem_cache_vira_erro_nunca_final(pedido_valido):
    def cai(_):
        raise ErroClima("sem_cache", "Não há dados de clima guardados para este local.", "NASA GPM IMERG Final e NASA POWER")

    r = secoes.calcular(_pedido(pedido_valido), simular=cai)
    RespostaCalculo.model_validate(r)
    assert r["estado_geral"] == "erro" and r["final"] is False
    (e,) = r["erros"]
    assert e == {"tipo": "erro", "codigo": "sem_cache", "mensagem": "Não há dados de clima guardados para este local.",
                 "origem": "NASA GPM IMERG Final e NASA POWER", "campo": None, "cache": {"disponivel": False, "obtido_em": None},
                 "acao": e["acao"]}
    b = r["culturas"][0]
    assert b["risco_hidrico"]["estado"] == "erro" and b["economia"]["estado"] == "indisponivel"
    assert b["economia"]["conteudo"] is None  # nenhum número parcial
    assert {f["estado"] for f in r["fontes"]} == {"falha"}
    assert "sem_resultado_final" in {a["codigo"] for a in r["avisos"]}


def test_estado_geral_regras():
    s = lambda e, o=True: {"estado": e, "obrigatoria": o}  # noqa: E731
    assert regras.estado_geral([s("disponivel")], [{"estado": "ok"}]) == "final"
    assert regras.estado_geral([s("disponivel")], [{"estado": "cache"}]) == "final_com_cache"
    assert regras.estado_geral([s("disponivel"), s("pendente")], []) == "incompleto"
    assert regras.estado_geral([s("erro"), s("pendente")], []) == "erro"
    assert regras.estado_geral([s("disponivel"), s("erro", False)], []) == "final"


def test_com_008_pendente_nada_e_final(resposta_real):
    assert resposta_real["estado_geral"] == "incompleto" and resposta_real["final"] is False
