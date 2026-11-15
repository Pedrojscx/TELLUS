"""Grupo "não sei" (achado da bateria e2e de 15/11/2026): o risco e a margem são calculados por grupo na recomendação,
mas a resposta ainda precisa listar as fontes de clima (e o cache) e o valor padrão das premissas editadas."""

from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.contrato import exemplos

PEDIDO = exemplos.PEDIDO_VALIDO | {"grupo": "nao_sei", "premissas_editadas": exemplos.PEDIDO_VALIDO["premissas_editadas"] + [
    {"modulo": "economia", "id": "preco_r_saca", "valor_novo": 70.0, "unidade": "R$/saca de 60 kg", "cultura": "milho_2a_safra"}]}


def test_nao_sei_lista_fontes_de_clima_e_padrao_das_premissas():
    r = TestClient(app).post("/api/contrato/calcular", json=PEDIDO)
    assert r.status_code == 200
    j = r.json()
    nomes = [f["fonte"] for f in j["fontes"]]
    assert any("IMERG" in n for n in nomes) and any("POWER" in n for n in nomes)
    assert all(f["secao"] == "recomendacao" for f in j["fontes"])
    milho = next(p for p in j["premissas_editadas"] if p["cultura"] == "milho_2a_safra" and p["id"] == "preco_r_saca")
    assert isinstance(milho["valor_padrao"], (int, float)) and milho["valor_padrao"] > 0  # padrão do Cepea, não nulo
    sorgo = next(p for p in j["premissas_editadas"] if p["cultura"] == "sorgo_granifero_2a_safra")
    assert sorgo["valor_padrao"] is None  # sorgo não tem indicador oficial (D-005): continua "sem padrão com fonte"
    assert j["recomendacao"]["estado"] == "disponivel"
    from tellus.contrato.modelos import RespostaCalculo
    RespostaCalculo.model_validate(j)  # a resposta continua dentro do contrato 1.2.0


def test_nao_sei_com_clima_em_cache_vira_final_com_cache():
    from tellus.contrato import regras, secoes

    def serie_cache(*_):
        prov = {"chuva": {"fonte": "NASA GPM IMERG Final", "obtido_em": "2026-11-01"},
                "power": {"fonte": "NASA POWER", "obtido_em": "2026-11-01"}}
        return [], {"proveniencia": prov, "origem_dados": "cache"}

    p = regras.normalizar_pedido(exemplos.PEDIDO_VALIDO | {"grupo": "nao_sei"})
    r = secoes.calcular(p, serie_clima=serie_cache)
    assert r["estado_geral"] == "final_com_cache"
    assert {f["estado"] for f in r["fontes"]} == {"cache"}
    assert any(a["codigo"] == "cache_usado" and "2026-11-01" in a["mensagem"] for a in r["avisos"])
