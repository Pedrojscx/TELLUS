from tellus.localizacao import servico
from tellus.localizacao.referencias import carregar


def _codigos(resultado):
    return {a["codigo"] for a in resultado["avisos"]}


def test_estacao_distante_no_oeste_do_amazonas():
    ref = carregar()
    r = servico.resolver(ref, -6.5, -69.0)
    est = next(x for x in r["referencias"] if x["tipo"] == "estacao_inmet")
    if est["distancia_km"] > ref.limite("estacao_distante_km"):
        assert "estacao_distante" in _codigos(r)
    else:
        assert "estacao_distante" not in _codigos(r)


def test_goiania_usa_praca_de_outro_municipio():
    r = servico.resolver(carregar(), -16.6869, -49.2648)
    assert "praca_outro_municipio" in _codigos(r)


def test_estacao_em_pane_mais_proxima_gera_aviso():
    ref = carregar()
    em_pane = next(e for e in ref.estacoes if e["situacao"] != "Operante")
    r = servico.resolver(ref, em_pane["lat"], em_pane["lon"])
    est = next(x for x in r["referencias"] if x["tipo"] == "estacao_inmet")
    assert est["identificador"] != em_pane["codigo"]
    assert "estacao_em_pane_ignorada" in _codigos(r)
