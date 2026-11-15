"""#96 T-065: pedido versionado e validado; geometria inválida não inicia cálculo."""

import pytest

from tellus.contrato import regras, secoes, versao

OBRIGATORIOS = ["area", "data_colheita_soja", "solo", "grupo", "metodologia"]
QUADRADO = [[-50.97, -17.79], [-50.96, -17.79], [-50.96, -17.78], [-50.97, -17.78], [-50.97, -17.79]]


def _erro(p) -> versao.ErroContrato:
    with pytest.raises(versao.ErroContrato) as e:
        regras.normalizar_pedido(p)
    return e.value


def test_pedido_completo_normalizado(pedido_valido):
    n = regras.normalizar_pedido(pedido_valido)
    assert n["area"]["confirmada"] is True and n["solo"]["textura"] == "argilosa"
    assert n["hash_pedido"] == regras.normalizar_pedido(pedido_valido)["hash_pedido"]


@pytest.mark.parametrize("campo", OBRIGATORIOS)
def test_campo_obrigatorio_ausente(pedido_valido, campo):
    del pedido_valido[campo]
    e = _erro(pedido_valido)
    assert e.codigo == "pedido_invalido" and campo in e.mensagem and e.campo.startswith(campo)


@pytest.mark.parametrize("ajuste,trecho", [
    ({"solo": {"textura": "argilosa", "cad_mm": 50}}, "exatamente um"),
    ({"solo": {"cad_mm": 0}}, "cad_mm"),
    ({"solo": {"granulometria": {"areia": 30, "silte": 15, "argila": 40}}}, "somando 100"),
    ({"grupo": "IV"}, "grupo"),
    ({"data_colheita_soja": "2027-02-30"}, "data_colheita_soja"),
    ({"metodologia": "cultura_escolhida"}, "cultura"),
    ({"cultura": "milho_2a_safra"}, "comparar_alternativas"),
    ({"campo_novo": 1}, "campo_novo"),
])
def test_dominios(pedido_valido, ajuste, trecho):
    assert trecho in _erro(pedido_valido | ajuste).mensagem


def test_area_nao_confirmada_nao_calcula(pedido_valido):
    pedido_valido["area"]["confirmada"] = False
    assert "confirmada" in _erro(pedido_valido).mensagem


def test_geometria_valida_aceita(pedido_valido):
    pedido_valido["area"] = {"tipo": "geometria", "id_geometria": "g1", "origem": "desenho", "confirmada": True,
                             "geometria": {"type": "Polygon", "coordinates": [QUADRADO]}}
    assert regras.normalizar_pedido(pedido_valido)["area"]["tipo"] == "geometria"


@pytest.mark.parametrize("coords,trecho", [
    ([QUADRADO[:-1]], "não fechado"),
    ([[[-50.97, -17.79], [-50.96, -17.78], [-50.97, -17.78], [-50.96, -17.79], [-50.97, -17.79]]], "cruza"),
    ([[[0, 0], [1, 1], [0, 0]]], "menos de 4"),
])
def test_geometria_invalida_nao_inicia_calculo(pedido_valido, monkeypatch, coords, trecho):
    chamado = []
    monkeypatch.setattr(secoes, "calcular", lambda *a, **k: chamado.append(1))
    pedido_valido["area"] = {"tipo": "geometria", "id_geometria": "g", "origem": "desenho", "confirmada": True,
                             "geometria": {"type": "Polygon", "coordinates": coords}}
    e = _erro(pedido_valido)
    assert e.codigo == "geometria_invalida" and trecho in e.mensagem and e.campo == "area.geometria"
    assert chamado == []


def test_limites_d009_hipotese_no_arquivo_unico():
    lim = regras.limites()
    for k, v in {"arquivo_max_bytes": 20971520, "vertices_total_max": 10000, "area_max_ha": 100000,
                 "processamento_prazo_s": 60, "lavouras_por_envio": 1}.items():
        assert lim[k]["valor"] == v and lim[k]["status"] == "hipotese" and lim[k]["decisao"] == "D-009"
    assert lim["vertices_por_anel_max"]["valor"] == 5000  # limite técnico da spec 001, inalterado


def _quadrado(lado_graus, n_lado=1, x0=-50.97, y0=-17.79):
    pts = [[x0 + lado_graus * i / n_lado, y0] for i in range(n_lado)] + [[x0 + lado_graus, y0 + lado_graus * i / n_lado] for i in range(n_lado)]
    pts += [[x0 + lado_graus - lado_graus * i / n_lado, y0 + lado_graus] for i in range(n_lado)] + [[x0, y0 + lado_graus - lado_graus * i / n_lado] for i in range(n_lado)]
    return pts + [list(pts[0])]  # cópia: o fechamento não pode ser o mesmo objeto do 1º ponto


def test_area_acima_do_limite(pedido_valido):
    pedido_valido["area"] = {"tipo": "geometria", "id_geometria": "g", "origem": "arquivo", "confirmada": True,
                             "geometria": {"type": "Polygon", "coordinates": [_quadrado(3.0)]}}  # ≈ 10 milhões de ha
    e = _erro(pedido_valido)
    assert e.codigo == "area_excedida" and e.campo == "geometria" and "Divida" in e.mensagem and e.origem == "pedido"


def test_vertices_total_acima_do_limite(pedido_valido):
    ns = [500] * 4 + [499]  # 5 anéis de 4n+1 vértices = 10.001 (limite + 1), cada um < 5.000
    partes = [[_quadrado(0.001, n, x0=-50.97 + k * 0.01)] for k, n in enumerate(ns)]
    assert sum(len(p[0]) for p in partes) == regras.limites()["vertices_total_max"]["valor"] + 1
    pedido_valido["area"] = {"tipo": "geometria", "id_geometria": "g", "origem": "arquivo", "confirmada": True,
                             "geometria": {"type": "MultiPolygon", "coordinates": partes}}
    e = _erro(pedido_valido)
    assert e.codigo == "vertices_excedidos" and "Simplifique" in e.mensagem and e.campo == "geometria"


def test_premissas_editadas_preservam_padrao(resposta_real):
    (p,) = resposta_real["premissas_editadas"]
    assert p["id"] == "preco_r_saca" and p["valor_novo"] == 55.0
    assert p["valor_padrao"] is None  # sorgo: preço padrão indisponível (D-005), nunca inventado
    assert p["origem_informada"] == "Cooperativa local de Rio Verde/GO"
    assert str(p["data_informada"]) == "2025-01-15"


def test_cotacao_informada_somente_na_premissa_de_preco(pedido_valido):
    cotacao = pedido_valido["premissas_editadas"][0]
    cotacao |= {"origem_informada": "  Cooperativa   local  ", "data_informada": "2025-01-15"}
    normalizada = regras.normalizar_pedido(pedido_valido)
    assert normalizada["premissas_editadas"][0]["origem_informada"] == "Cooperativa local"

    cotacao["id"] = "custo_item.1"
    assert "só valem para a premissa de preço" in _erro(pedido_valido).mensagem


@pytest.mark.parametrize("ausente", ["origem_informada", "data_informada"])
def test_cotacao_informada_exige_origem_e_data_juntas(pedido_valido, ausente):
    pedido_valido["premissas_editadas"][0] |= {
        "origem_informada": "Cooperativa local", "data_informada": "2025-01-15"
    }
    del pedido_valido["premissas_editadas"][0][ausente]
    assert "juntas" in _erro(pedido_valido).mensagem


def test_cotacao_informada_vira_proveniencia_rastreavel(resposta_real):
    sorgo = next(c for c in resposta_real["culturas"] if c["cultura"] == "sorgo_granifero_2a_safra")
    prov = next(p for p in sorgo["economia"]["proveniencia"] if p["id"] == "preco_informado")
    assert prov["fonte"] == "Cooperativa local de Rio Verde/GO"
    assert prov["periodo"] == prov["obtido_em"] == "2025-01-15"
    assert prov["situacao"] == "informada_pelo_produtor"


def test_padrao_preenchido_quando_existe(pedido_valido):
    pedido_valido |= {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra",
                      "premissas_editadas": [{"modulo": "economia", "id": "preco_r_saca", "valor_novo": 70, "unidade": "R$/saca de 60 kg"},
                                             {"modulo": "motor", "id": "armazenamento_inicial_frac", "valor_novo": 0.5, "unidade": "fração da CAD"}]}
    r = secoes.calcular(regras.normalizar_pedido(pedido_valido))
    pad = {p["id"]: p["valor_padrao"] for p in r["premissas_editadas"]}
    assert pad["preco_r_saca"] == r["culturas"][0]["economia"]["conteudo"]["premissas"]["preco"]["valor"]
    assert pad["armazenamento_inicial_frac"] == 1.0


def _geo(partes):
    return {"tipo": "geometria", "id_geometria": "g", "origem": "arquivo", "confirmada": True,
            "geometria": {"type": "MultiPolygon", "coordinates": partes}}


def test_vertices_total_exatamente_no_limite_passa(pedido_valido):
    ns = [625] * 3 + [624]  # 4 anéis de 4n+1 vértices = 10.000 no total (o limite), cada um < 5.000
    partes = [[_quadrado(0.001, n, x0=-50.97 + k * 0.01)] for k, n in enumerate(ns)]
    assert sum(len(p[0]) for p in partes) == regras.limites()["vertices_total_max"]["valor"]
    pedido_valido["area"] = _geo(partes)
    assert regras.normalizar_pedido(pedido_valido)


@pytest.mark.parametrize("lado,passa", [(0.28, True), (0.30, False)])  # ≈ 91 mil ha × ≈ 105 mil ha em Rio Verde
def test_area_perto_do_limite(pedido_valido, lado, passa):
    pedido_valido["area"] = _geo([[_quadrado(lado)]])
    if passa:
        assert regras.normalizar_pedido(pedido_valido)
    else:
        assert _erro(pedido_valido).codigo == "area_excedida"
