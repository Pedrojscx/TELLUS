"""#97 T-066: resposta rastreável; todo número com proveniência completa (SC-002)."""

import json
import re

from tellus.contrato import regras
from tellus.contrato.modelos import RespostaCalculo


def test_resposta_real_valida_no_modelo(resposta_real):
    RespostaCalculo.model_validate(resposta_real)
    assert [b["cultura"] for b in resposta_real["culturas"]] == ["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"]


def test_todo_numero_tem_proveniencia_completa(resposta_real):
    assert regras.numeros_sem_proveniencia(resposta_real) == []
    total = sum(1 for _, s in regras._secoes(resposta_real) for _ in regras.numeros(s.get("conteudo") or {}))
    assert total > 1000  # o teste percorre de fato a resposta inteira (por_ano de 3 culturas)


def test_numero_sem_cobertura_e_acusado(resposta_real):
    resposta_real["culturas"][0]["economia"]["conteudo"]["numero_sem_fonte"] = 42
    assert regras.numeros_sem_proveniencia(resposta_real) == ["culturas.0.economia.conteudo.numero_sem_fonte = 42 sem proveniência"]


def test_proveniencia_incompleta_e_acusada(resposta_real):
    resposta_real["culturas"][0]["economia"]["proveniencia"][0]["qualidade"] = " "
    falhas = regras.numeros_sem_proveniencia(resposta_real)
    assert any("incompleta" in f for f in falhas) and any("custo" in f for f in falhas)


def test_seis_campos_da_constituicao(resposta_real):
    for b in resposta_real["culturas"]:
        for nome in ("risco_hidrico", "economia"):
            for p in b[nome]["proveniencia"]:
                assert all(p[c].strip() for c in regras.CAMPOS_PROVENIENCIA), (nome, p["id"])


def test_economia_e_a_saida_real_da_007(resposta_real):
    milho = resposta_real["culturas"][0]["economia"]
    assert milho["estado"] == "disponivel"
    c = milho["conteudo"]
    assert c["custo_conab"]["praca"] == "Rio Verde-GO" and c["custo_conab"]["total_nivel_r_ha"] == 5889.09
    assert set(c["cenarios"]) == {"conservador", "central", "favoravel"}
    ids = {p["id"] for p in milho["proveniencia"]}
    assert {"conab_custo", "conab_produtividade", "preco", "perda_motor", "percentis", "calculo_margem"} <= ids


def test_sorgo_sem_preco_padrao_mas_editado_tem_margem(resposta_real):
    s = resposta_real["culturas"][1]["economia"]
    assert s["estado"] == "disponivel" and s["conteudo"]["premissas"]["preco"]["status"] == "indisponivel"
    assert s["conteudo"]["premissas"]["preco"]["valor_usado"] == 55.0
    assert "premissas_do_produtor" in {p["id"] for p in s["proveniencia"]}


def test_cobertura_sem_custo_fica_indisponivel_com_aviso(resposta_real):
    c = resposta_real["culturas"][2]["economia"]
    assert c["estado"] == "indisponivel" and c["avisos"]
    assert all(v["margem_r_ha"] is None for v in c["conteudo"]["cenarios"].values())


def test_008_pendente_sem_campos_inventados(resposta_real):
    rec = resposta_real["recomendacao"]
    assert rec["estado"] == "pendente" and rec["conteudo"] is None and rec["proveniencia"] == []
    texto = json.dumps(resposta_real, ensure_ascii=False)
    assert not re.search(r'"(ranking|posicao|ordem|alternativa_recomendada|recomendada)"', texto)


def test_versoes_de_entradas_e_contrato(resposta_real):
    v = resposta_real["versoes"]
    assert v["contrato"] == "1.0.0" and v["hash_pedido"] == resposta_real["pedido"]["hash_pedido"]
    assert all(v["modulos"][k] for k in v["modulos"])
    assert len(v["modulos"]) == 6


def test_sem_segredo_na_resposta(resposta_real):
    texto = json.dumps(resposta_real, ensure_ascii=False).lower()
    assert "earthdata_token" not in texto and "bearer" not in texto and not re.search(r"eyj[a-z0-9_-]{20,}", texto)
