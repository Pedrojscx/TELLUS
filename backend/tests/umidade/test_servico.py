import json

import pytest

from tellus.umidade import cliente, regras, servico

from .conftest import CEL_M09, LAT, LON

CAMPOS_METADADO = ("produto", "versao", "celula", "periodo", "unidade", "qualidade", "resolucao", "aviso_escala")


def _percorrer_itens(resp):
    assert resp["itens"], "resposta sem itens"
    for it in resp["itens"]:
        for campo in CAMPOS_METADADO:
            assert it.get(campo) not in (None, "", {}), f"falta {campo}"
        assert it["aviso_escala"]["espacial"] and it["aviso_escala"]["temporal"]
        assert it["natureza"] == "contexto_regional" and it["uso"] == regras.USO
        assert regras.validar_item(it) == []
        yield it


# ---------------------------------------------------------------- SC-001 / #93 / #94


def test_valor_valido_traz_todos_os_metadados_e_aviso(cache_sintetico):
    r = servico.contexto(LAT, LON, data="2025-01-10", dir_cache=cache_sintetico)
    itens = list(_percorrer_itens(r))
    assert len(itens) == 1
    it = itens[0]
    assert it["estado"] == "disponivel" and it["valor"] == 0.3124
    assert it["produto"]["id"] == "SPL3SMP_E"
    assert it["versao"] == {"valor": "006", "situacao": "confirmado_no_arquivo", "fonte": "fixture sintética"}
    assert (it["celula"]["linha"], it["celula"]["coluna"]) == CEL_M09
    assert it["celula"]["tamanho_km"] == 9.01 and it["celula"]["distancia_km"] == pytest.approx(5.39, abs=0.01)
    assert it["periodo"]["inicio"].startswith("2025-01-10") and it["periodo"]["variante"] == "AM"
    assert it["unidade"]["valor"] == "cm³/cm³" and it["unidade"]["situacao"] == "confirmado_no_arquivo"
    assert it["qualidade"]["recomendada"] is True
    assert "9 km" in it["resolucao"]["espacial"] and "diária" in it["resolucao"]["temporal"]


def test_sc001_todo_valor_em_qualquer_cenario_tem_aviso(cache_sintetico):
    """SC-001: 100% dos valores (todos os dias e variantes) com aviso de escala."""
    total = 0
    for variante in ("AM", "PM"):
        r = servico.contexto(LAT, LON, variante=variante, inicio="2025-01-09", fim="2025-01-15", dir_cache=cache_sintetico)
        total += len(list(_percorrer_itens(r)))
    assert total == 14


def test_qualidade_nao_recomendada_mostra_valor_com_aviso(cache_sintetico):
    r = servico.contexto(LAT, LON, data="2025-01-12", dir_cache=cache_sintetico)
    it = r["itens"][0]
    assert it["estado"] == "disponivel" and it["qualidade"]["recomendada"] is False
    assert "qualidade_nao_recomendada" in {a["codigo"] for a in r["avisos"]}


# ---------------------------------------------------------------- SC-002 / #94


@pytest.mark.parametrize("dia,motivo", [("2025-01-11", "sem_dado_na_celula"), ("2025-01-13", "sem_registro")])
def test_sc002_celula_sem_dado_fica_indisponivel_sem_substituicao(cache_sintetico, dia, motivo):
    r = servico.contexto(LAT, LON, data=dia, dir_cache=cache_sintetico)
    (it,) = list(_percorrer_itens(r))
    assert it["estado"] == "indisponivel" and it["valor"] is None
    assert it["motivo"].startswith(motivo) and "vizinha" in it["motivo"]
    assert (it["celula"]["linha"], it["celula"]["coluna"]) == CEL_M09  # a mesma célula, nunca outra
    assert "celula_indisponivel" in {a["codigo"] for a in r["avisos"]}


def test_periodo_nao_preenche_dia_ausente_com_vizinho(cache_sintetico):
    r = servico.contexto(LAT, LON, inicio="2025-01-10", fim="2025-01-14", dir_cache=cache_sintetico)
    estados = [(i["periodo"]["inicio"][:10], i["estado"], i["valor"]) for i in r["itens"]]
    assert estados == [
        ("2025-01-10", "disponivel", 0.3124), ("2025-01-11", "indisponivel", None),
        ("2025-01-12", "disponivel", 0.287), ("2025-01-13", "indisponivel", None),
        ("2025-01-14", "disponivel", 0.2755),
    ]
    assert r["regra_periodo"] == {"valor": "dias_pedidos_sem_agregacao", "situacao": "hipotese", "decisao": "D-008"}
    assert not any(k in json.dumps(r) for k in ("media", "média"))


def test_fora_da_grade_e_indisponivel(tmp_path):
    r = servico.contexto(87.0, 10.0, dir_cache=tmp_path)
    (it,) = list(_percorrer_itens(r))
    assert it["estado"] == "indisponivel" and it["motivo"].startswith("fora_da_grade")


# ---------------------------------------------------------------- degradação (Princípio VII)


def _fonte_fora(*_a, **_k):
    raise cliente.FonteIndisponivel("timeout simulado")


def test_fonte_fora_com_cache_usa_cache_e_avisa_data(cache_sintetico):
    r = servico.contexto(LAT, LON, data="2025-01-10", dir_cache=cache_sintetico, buscar=_fonte_fora)
    av = {a["codigo"]: a["mensagem"] for a in r["avisos"]}
    assert "cache_usado" in av and "2026-11-15" in av["cache_usado"] and "SPL3SMP_E" in av["cache_usado"]
    assert r["itens"][0]["valor"] == 0.3124


def test_fonte_fora_sem_cache_da_erro_que_nomeia_origem(tmp_path):
    with pytest.raises(servico.ErroUmidade) as e:
        servico.contexto(LAT, LON, data="2025-01-10", dir_cache=tmp_path, buscar=_fonte_fora)
    assert e.value.codigo == "fonte_indisponivel" and e.value.status == 503
    assert "NASA SMAP SPL3SMP_E" in e.value.origem and "NSIDC" in e.value.origem
    assert "não respondeu" in e.value.mensagem


def test_sem_cache_offline_da_erro_legivel(tmp_path):
    with pytest.raises(servico.ErroUmidade) as e:
        servico.contexto(LAT, LON, dir_cache=tmp_path)
    assert e.value.codigo == "sem_cache" and "SMAP" in e.value.origem
    assert "preparar_umidade.py" in e.value.mensagem


# ---------------------------------------------------------------- decisão pendente (#70)


def test_produto_e_janela_marcados_como_hipotese(cache_sintetico):
    r = servico.contexto(LAT, LON, dir_cache=cache_sintetico)
    assert r["produto"]["id"] == "SPL3SMP_E" and r["produto"]["situacao"] == "hipotese"
    assert r["produto"]["selecionado_por"] == "hipotese_operacional_do_prototipo"
    rp = r["regra_periodo"]
    assert rp["situacao"] == "hipotese" and rp["janela_dias"] == 30 and rp["decisao"] == "D-008"
    assert r["decisoes_pendentes"][0]["estado"] == "decisao_pendente" and r["decisoes_pendentes"][0]["issue"].endswith("/70")
    assert {"decisao_pendente", "janela_hipotese"} <= {a["codigo"] for a in r["avisos"]}


def test_janela_30_dias_so_observacoes_validas_com_data_e_contagem(cache_sintetico):
    r = servico.contexto(LAT, LON, dir_cache=cache_sintetico)
    rp = r["regra_periodo"]
    assert (rp["inicio"], rp["fim"]) == ("2024-12-16", "2025-01-14")  # fim = último dia do cache, não o relógio
    assert rp["contagem"] == {"observacoes_validas": 3, "registros_sem_dado": 1,
                              "registros_qualidade_nao_recomendada": 1, "dias_sem_registro": 26,
                              "passagens_possiveis": 60}
    obs = [(i["periodo"]["data"], i["periodo"]["variante"], i["valor"]) for i in _percorrer_itens(r)]
    assert obs == [("2025-01-10", "AM", 0.3124), ("2025-01-10", "PM", 0.298), ("2025-01-14", "AM", 0.2755)]
    assert all(i["qualidade"]["recomendada"] is True for i in r["itens"])


def test_janela_parametrizavel_e_sem_validas_fica_indisponivel(cache_sintetico):
    r = servico.contexto(LAT, LON, janela_dias=2, variante="PM", dir_cache=cache_sintetico)
    (it,) = list(_percorrer_itens(r))  # PM só tem 2025-01-10; janela de 2 dias termina em 2025-01-10
    assert it["valor"] == 0.298 and r["regra_periodo"]["janela_dias"] == 2
    r = servico.contexto(LAT, LON, janela_dias=1, variante="AM", dir_cache=cache_sintetico)
    assert r["itens"][0]["estado"] == "disponivel"


def test_produto_pedido_continua_hipotese(cache_sintetico):
    r = servico.contexto(LAT, LON, produto="SPL3SMP_E", variante="PM", data="2025-01-10", dir_cache=cache_sintetico)
    assert r["produto"]["situacao"] == "hipotese" and r["produto"]["selecionado_por"] == "pedido"
    assert r["variante"]["situacao"] == "documentado_na_ficha"
    assert r["itens"][0]["valor"] == 0.298


def test_produto_desconhecido(cache_sintetico):
    with pytest.raises(servico.ErroUmidade) as e:
        servico.contexto(LAT, LON, produto="SMOS", dir_cache=cache_sintetico)
    assert e.value.codigo == "produto_desconhecido" and e.value.status == 422


def test_metadado_desconhecido_nunca_vira_confirmado(cache_l4):
    """#93: cache L4 sem versão, sem unidade e sem flag → desconhecido/documentado, nunca confirmado."""
    r = servico.contexto(LAT, LON, produto="SPL4SMGP", data="2025-01-10", dir_cache=cache_l4)
    (it,) = list(_percorrer_itens(r))
    assert it["versao"]["valor"] is None and it["versao"]["situacao"] == "desconhecido"
    assert it["unidade"] == {"valor": "m³/m³", "situacao": "documentado_na_ficha", "fonte": "ficha do produto"}
    assert it["qualidade"]["situacao"] == "desconhecido" and it["qualidade"]["recomendada"] is None
    assert it["periodo"]["fim"] == "2025-01-10T03:00:00.000Z"


# ---------------------------------------------------------------- geometria, sintético e determinismo


def test_geometria_que_toca_duas_celulas_gera_itens_separados(cache_sintetico):
    # Célula vizinha a leste (1059, 1383) também tem cache, para provar que nada é misturado.
    regs = [{**r, "valor": "0.100000"} for r in cliente.ler_cache(cache_sintetico, "SPL3SMP_E", "EASE2_M09", *CEL_M09)[0]]
    meta = cliente.ler_cache(cache_sintetico, "SPL3SMP_E", "EASE2_M09", *CEL_M09)[1]
    cliente.gravar_cache(cache_sintetico, "SPL3SMP_E", "EASE2_M09", 1059, 1383, regs, meta)
    clat, clon = regras.centro_celula(1059, 1382, 3856, 1624)
    borda = clon + 0.0467  # metade de uma célula de 9 km em lon ≈ 0,0467°
    poly = {"type": "Polygon", "coordinates": [[[borda - 0.01, clat - 0.01], [borda + 0.01, clat - 0.01],
                                                [borda + 0.01, clat + 0.01], [borda - 0.01, clat + 0.01], [borda - 0.01, clat - 0.01]]]}
    r = servico.contexto(geometria=poly, data="2025-01-10", dir_cache=cache_sintetico)
    assert [(c["linha"], c["coluna"]) for c in r["celulas"]] == [(1059, 1382), (1059, 1383)]
    assert sum(c["fracao_da_area"] for c in r["celulas"]) == pytest.approx(1.0)
    assert sorted(i["valor"] for i in r["itens"]) == [0.1, 0.3124]  # um item por célula, sem média


def test_dado_sintetico_e_declarado(cache_sintetico):
    r = servico.contexto(LAT, LON, data="2025-01-10", dir_cache=cache_sintetico)
    assert r["dado_sintetico"] is True and r["origem_dados"] == "fixture_sintetica"
    assert "dado_sintetico" in {a["codigo"] for a in r["avisos"]}


def test_determinismo_mesmo_pedido_mesmo_cache(cache_sintetico):
    a = servico.contexto(LAT, LON, inicio="2025-01-09", fim="2025-01-15", dir_cache=cache_sintetico)
    b = servico.contexto(LAT, LON, inicio="2025-01-09", fim="2025-01-15", dir_cache=cache_sintetico)
    assert json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def test_periodo_invalido(cache_sintetico):
    for kw in ({"data": "10/01/2025"}, {"inicio": "2025-02-01", "fim": "2025-01-01"}, {"inicio": "2025-01-01", "fim": "2025-03-01"}):
        with pytest.raises(servico.ErroUmidade) as e:
            servico.contexto(LAT, LON, dir_cache=cache_sintetico, **kw)
        assert e.value.codigo == "periodo_invalido"


def test_produtos_lista_candidatos_pendentes():
    p = servico.produtos()
    assert [x["id"] for x in p["produtos"]] == ["SPL3SMP", "SPL3SMP_E", "SPL4SMGP"]
    assert {x["situacao"] for x in p["produtos"]} == {"decisao_pendente"}
    assert {x["versao"] for x in p["produtos"]} == {"009", "006", "008"}
