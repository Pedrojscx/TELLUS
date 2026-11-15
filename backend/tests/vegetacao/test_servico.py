"""Critérios de aceite da spec 009 (#51, #91, #92) sobre o cache sintético."""

import json

import pytest

from tellus.vegetacao import servico
from tellus.vegetacao.servico import ErroVegetacao

from .conftest import AUSENTE_MOD, LAT, LON, NUVEM_MOD, POLIGONO

SEM_TOKEN: dict[str, str] = {}
PROIBIDOS = ("produtividade", "previsão", "previsao", "rendimento", "kg/ha", "sc/ha")
CAMPOS_PROV = ("produto", "versao", "periodo", "resolucao", "unidade", "qualidade", "area", "escala", "limitacao", "origem", "status")


TUDO = {"inicio": "2023-01-01", "fim": "2024-12-31"}
AMBOS = ["MOD13Q1", "MYD13Q1"]


def _ctx(cache, **kw):
    kw.setdefault("dir_series", None)  # isola do repositório: só o cache sintético
    return servico.contexto(lat=LAT, lon=LON, dir_cache=cache, ambiente=kw.pop("ambiente", SEM_TOKEN), **kw)


def _fonte(r, produto):
    return next(f for f in r["fontes"] if f["produto"] == produto)


def _itens_com_valor(r):
    for f in r["fontes"]:
        yield from f["serie"]
        yield from f["indicadores"]


def _numeros_fora_de_parametros(no, caminho=""):
    """Todo dict com 'valor' numérico ou nulo fora de 'parametros' (os parâmetros têm status próprio)."""
    if isinstance(no, dict):
        if "valor" in no and not caminho.startswith("parametros"):
            yield caminho, no
        for k, v in no.items():
            yield from _numeros_fora_de_parametros(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(no, list):
        for i, v in enumerate(no):
            yield from _numeros_fora_de_parametros(v, f"{caminho}[{i}]")


# ---------------------------------------------------------------- SC-001 / FR-002 (#91)


def test_proveniencia_completa_em_toda_observacao_e_indicador(cache_ponto):
    r = _ctx(cache_ponto, produtos=AMBOS, **TUDO)
    itens = list(_itens_com_valor(r))
    assert len(itens) > 50
    encontrados = list(_numeros_fora_de_parametros(r))
    assert len(encontrados) == len(itens)  # nenhum número escapa do registro de proveniência
    for caminho, item in encontrados:
        faltam = [c for c in CAMPOS_PROV if item.get(c) in (None, "", {}, [])]
        assert not faltam, f"{caminho} sem {faltam}"
        assert item["periodo"]["inicio"] and item["periodo"]["fim"], caminho
        assert item["resolucao"]["espacial_m"] and item["resolucao"]["temporal"], caminho
        assert item["area"]["chave"] and item["area"]["n_pixels"] >= 1, caminho
        assert "não é medição" in item["escala"], caminho
        assert item["origem"]["obtido_em"] and item["origem"]["nome"], caminho
        assert "estado" in item["qualidade"] or "n_validas" in item["qualidade"], caminho


def test_serie_valida_traz_metadados_do_produto(cache_ponto):
    r = _ctx(cache_ponto, produtos=AMBOS, **TUDO)
    mod = _fonte(r, "MOD13Q1")
    o = next(x for x in mod["serie"] if x["data"] == "2023-02-02")
    assert o["valor"] is not None and o["qualidade"]["estado"] == "valida"
    assert (o["produto"], o["versao"], o["doi"]) == ("MOD13Q1", "061", "10.5067/MODIS/MOD13Q1.061")
    assert o["periodo"] == {"inicio": "2023-02-02", "fim": "2023-02-17"}
    assert o["resolucao"]["temporal"] == "composição de 16 dias"
    assert o["unidade"].startswith("adimensional")
    assert _fonte(r, "MYD13Q1")["serie"][0]["data"] == "2023-01-09"


def test_agregacao_mensal_nao_perde_metadado(cache_ponto):
    mod = _fonte(_ctx(cache_ponto, **TUDO), "MOD13Q1")
    meses = [i for i in mod["indicadores"] if i["nome"] == "media_mensal"]
    assert [m["mes"] for m in meses] == list(range(1, 13))
    jan = meses[0]
    assert jan["produto"] == "MOD13Q1" and jan["versao"] == "061"
    assert jan["periodo"] == {"inicio": "2023-01-01", "fim": "2024-12-31"}
    # janeiro: 2 composições/ano × 2 anos = 4; 2023-01-17 é nuvem → 3 válidas
    assert jan["qualidade"]["n_validas"] == 3 and jan["qualidade"]["n_total"] == 4
    meses_c = next(i for i in mod["indicadores"] if i["nome"] == "meses_cobertos")
    assert meses_c["valor"] == 24.0 and meses_c["unidade"] == "meses"


# ---------------------------------------------------------------- cenário 2 / FR-003 (#92)


def test_nuvem_e_qa_ruim_viram_lacuna_sem_interpolar(cache_ponto):
    serie = {o["data"]: o for o in _fonte(_ctx(cache_ponto, **TUDO), "MOD13Q1")["serie"]}
    esperado = {"2023-01-17": "nuvem", "2024-02-02": "nuvem", "2023-03-06": "nuvem_adjacente", "2024-06-25": "neve_gelo",
                AUSENTE_MOD: "ausente_no_cache"}
    assert set(esperado) == set(NUVEM_MOD) | {AUSENTE_MOD}
    for d, motivo in esperado.items():
        o = serie[d]
        assert o["valor"] is None, d
        assert o["qualidade"] == {"estado": "lacuna", "motivo": motivo, "cobertura_valida": 0.0,
                                  "fracao_por_motivo": {motivo: 1.0}}, d
    validas = [o for o in serie.values() if o["valor"] is not None]
    assert all(o["qualidade"]["estado"] == "valida" and o["qualidade"]["motivo"] is None for o in validas)
    assert len(serie) == 46 and len(validas) == 41


def test_poligono_um_pixel_nublado_vira_lacuna_da_area(cache_poligono):
    cache, ident, pesos = cache_poligono
    r = servico.contexto(geometria=POLIGONO, id_geometria=ident, dir_cache=cache, ambiente=SEM_TOKEN, dir_series=None, **TUDO)
    mod = _fonte(r, "MOD13Q1")
    assert mod["area"]["n_pixels"] == len(pesos) > 1
    assert r["area"]["tipo"] == "geometria" and r["area"]["area_ha"] > 0
    o = next(x for x in mod["serie"] if x["data"] == "2023-01-17")
    assert o["valor"] is None and o["qualidade"]["motivo"] == "nuvem"
    assert 0 < o["qualidade"]["cobertura_valida"] < 1


def test_geometria_sem_confirmacao_e_recusada(cache_poligono):
    cache, _, _ = cache_poligono
    with pytest.raises(ErroVegetacao) as e:
        servico.contexto(geometria=POLIGONO, id_geometria="outro", dir_cache=cache, ambiente=SEM_TOKEN)
    assert e.value.codigo == "geometria_nao_confirmada"


# ---------------------------------------------------------------- Edge Case: HLS (#51, #92)


def test_hls_sem_credencial_nao_bloqueia_modis(cache_ponto):
    r = _ctx(cache_ponto, ambiente={})
    hls = _fonte(r, "HLS")
    assert hls["estado"] == "indisponivel" and hls["motivo"]["codigo"] == "sem_credencial"
    assert "Earthdata" in hls["motivo"]["mensagem"] and "MODIS" in hls["motivo"]["mensagem"]
    assert _fonte(r, "MOD13Q1")["estado"] == "disponivel"
    assert any(a["codigo"] == "hls_indisponivel" for a in r["avisos"])


def test_hls_com_credencial_mas_sem_cache(cache_ponto):
    hls = _fonte(_ctx(cache_ponto, ambiente={"EARTHDATA_TOKEN": "x"}), "HLS")
    assert hls["estado"] == "indisponivel" and hls["motivo"]["codigo"] == "sem_cache"


def test_hls_em_cache_aplica_fmask(cache_ponto_hls):
    hls = _fonte(_ctx(cache_ponto_hls, **TUDO), "HLS")
    assert hls["estado"] == "disponivel"
    assert hls["suficiencia"]["estado"] == "insuficiente"  # 2 cenas válidas < 6
    por = {(o["data"], o["sensor"]): o for o in hls["serie"]}
    assert por[("2024-01-10", "S30")]["valor"] == 0.7143 and por[("2024-01-10", "S30")]["produto"] == "HLSS30"
    assert por[("2024-01-13", "L30")]["valor"] is None and por[("2024-01-13", "L30")]["qualidade"]["motivo"] == "nuvem"
    assert por[("2024-01-20", "S30")]["qualidade"]["motivo"] == "sombra_nuvem"
    assert por[("2024-02-04", "L30")]["valor"] == 0.7143
    assert por[("2024-01-10", "S30")]["resolucao"]["espacial_m"] == 30


def test_sem_nenhuma_fonte_erro_legivel_nomeia_origens(tmp_path):
    with pytest.raises(ErroVegetacao) as e:
        _ctx(tmp_path)
    assert e.value.codigo == "sem_cache" and "MOD13Q1" in e.value.origem and "HLS" in e.value.origem
    assert "não bloqueia" in e.value.mensagem


# ---------------------------------------------------------------- SC-002 / FR-004 (#51)


def _textos(no):
    if isinstance(no, dict):
        for k, v in no.items():
            yield str(k)
            yield from _textos(v)
    elif isinstance(no, list):
        for v in no:
            yield from _textos(v)
    elif isinstance(no, str):
        yield no


@pytest.mark.parametrize("fixture", ["cache_ponto", "cache_ponto_hls"])
def test_nenhum_texto_de_produtividade_ou_previsao(fixture, request):
    r = _ctx(request.getfixturevalue(fixture), produtos=AMBOS, **TUDO)
    r_hls = _ctx(request.getfixturevalue(fixture), ambiente={}, inicio="2024-12-01")
    for resp in (r, r_hls):
        for t in _textos(resp):
            baixo = t.lower()
            for p in PROIBIDOS:
                assert p not in baixo, f"termo proibido '{p}' em: {t}"
    assert r["finalidade"] == "contexto_historico"


def test_referencias_sem_termos_proibidos():
    for p in servico.DIR_REF.glob("*.json"):
        baixo = p.read_text(encoding="utf-8").lower()
        for termo in PROIBIDOS:
            assert termo not in baixo, f"{termo} em {p.name}"


# ---------------------------------------------------------------- decisão pendente (#69)


def test_proposta_69_marcada_como_hipotese(cache_ponto):
    r = _ctx(cache_ponto)
    par = r["parametros"]
    assert par["decisao"]["issue"] == "#69"
    for k in ("produtos_modis", "indice", "janela_meses", "minimo_composicoes_validas",
              "regra_qualidade_modis", "regra_qualidade_hls", "cobertura_minima_area"):
        assert par[k]["status"] == "hipotese", k
    assert (par["indice"]["valor"], par["janela_meses"]["valor"], par["minimo_composicoes_validas"]["valor"]) == ("ndvi", 12, 6)
    assert par["produtos_modis"]["valor"] == ["MOD13Q1"]
    assert "Tabela 4" in par["regra_qualidade_modis"]["fonte"] and "3.10" in par["regra_qualidade_modis"]["fonte"]
    for item in _itens_com_valor(r):
        for k in ("indice", "regra_qualidade", "janela_meses", "minimo_composicoes_validas"):
            assert item["status"][k]["status"] == "hipotese"
    assert any(a["codigo"] == "decisao_pendente" for a in r["avisos"])
    assert any(a["codigo"] == "dado_sintetico" for a in r["avisos"])


def test_evi_escolhido_pelo_pedido(cache_ponto):
    r = _ctx(cache_ponto, indice="evi")
    o = next(x for x in _fonte(r, "MOD13Q1")["serie"] if x["valor"] is not None)
    assert o["indice"] == "evi"
    with pytest.raises(ErroVegetacao):
        _ctx(cache_ponto, indice="savi")


def test_janela_padrao_ultimos_12_meses_e_suficiencia(cache_ponto):
    r = _ctx(cache_ponto)
    assert [f["produto"] for f in r["fontes"]] == ["MOD13Q1", "HLS"]
    mod = _fonte(r, "MOD13Q1")
    datas = [o["data"] for o in mod["serie"]]
    # última composição do cache: 2024-12-18 → janela (2023-12-19, 2024-12-18]
    assert datas[0] == "2024-01-01" and datas[-1] == "2024-12-18" and len(datas) == 23
    assert mod["suficiencia"] == {
        "estado": "suficiente", "n_validas": 21, "minimo": 6, "status": "hipotese",
        "mensagem": mod["suficiencia"]["mensagem"],
    }


def test_serie_insuficiente_explicita(cache_ponto):
    r = _ctx(cache_ponto, inicio="2024-01-01", fim="2024-03-31")
    mod = _fonte(r, "MOD13Q1")
    assert mod["suficiencia"]["estado"] == "insuficiente" and mod["suficiencia"]["n_validas"] == 5
    assert any(a["codigo"] == "mod13q1_insuficiente" for a in r["avisos"])
    assert sum(o["valor"] is None for o in mod["serie"]) == 1  # 2024-02-02 nuvem continua lacuna


def test_referencia_versionada_quando_nao_ha_cache(tmp_path, cache_ponto):
    r = _ctx(tmp_path / "vazio", dir_series=cache_ponto)
    assert _fonte(r, "MOD13Q1")["origem"]["tipo"] == "referencia_versionada"


def test_recorte_de_periodo(cache_ponto):
    mod = _fonte(_ctx(cache_ponto, inicio="2024-01-01", fim="2024-03-31"), "MOD13Q1")
    assert [o["data"] for o in mod["serie"]][:2] == ["2024-01-01", "2024-01-17"]
    assert all("2024-01-01" <= o["data"] <= "2024-03-31" for o in mod["serie"])
    with pytest.raises(ErroVegetacao):
        _ctx(cache_ponto, inicio="2024-13-01")


# ---------------------------------------------------------------- Princípio III


def test_determinismo_mesmo_pedido_mesmo_cache(cache_ponto_hls):
    a = json.dumps(_ctx(cache_ponto_hls), sort_keys=True, ensure_ascii=False)
    b = json.dumps(_ctx(cache_ponto_hls), sort_keys=True, ensure_ascii=False)
    assert a == b


def test_cache_alterado_gera_aviso(cache_ponto):
    p = cache_ponto / servico.chave_ponto(LAT, LON) / "MOD13Q1.csv"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    r = _ctx(cache_ponto)
    assert any(a["codigo"] == "cache_alterado" for a in r["avisos"])
