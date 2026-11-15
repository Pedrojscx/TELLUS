"""Spec 014 (#113, #114, #115): mensagens do backend em inglês pelo catálogo, sem mudar números nem códigos."""

import copy

import pytest
from fastapi.testclient import TestClient

from tellus import i18n
from tellus.api.app import app
from tellus.contrato import exemplos
from tellus.umidade import servico as umidade

REF_SMAP = umidade.RAIZ / "referencias" / "umidade"
PEDIDO = exemplos.PEDIDO_VALIDO | {"grupo": "nao_sei", "contextos": {"vegetacao": True, "umidade": True}}
PROIBIDAS = ("forecast", "will rain", "predicted yield", "guaranteed")


def test_normaliza_idioma():
    assert i18n.normalizar_idioma("en-US,en;q=0.9") == "en"
    assert i18n.normalizar_idioma("pt-BR") == i18n.normalizar_idioma(None) == i18n.normalizar_idioma("es") == "pt-BR"


def test_frase_exata_e_modelo_com_campos():
    assert i18n.traduzir("plantio mais cedo", "en") == "earliest planting"
    # o nome informado pelo produtor é copiado como veio; a data também
    assert (i18n.traduzir("Preço informado pelo produtor (Cooperativa de Rio Verde, 2025-01-15)", "en")
            == "Price provided by the farmer (Cooperativa de Rio Verde, 2025-01-15)")
    # lista: cada item passa pelo catálogo
    assert (i18n.traduzir("O resultado usa hipóteses: Fração de esgotamento sem estresse (p); Kc da entressafra (palhada).", "en")
            == "The result uses assumptions: Depletion fraction without stress (p); Off-season Kc (straw mulch).")


def test_sem_traducao_marca_pt_e_nunca_some():
    assert i18n.traduzir("Uma frase nova que ninguém traduziu.", "en") == "(PT) Uma frase nova que ninguém traduziu."
    assert i18n.traduzir("Uma frase nova que ninguém traduziu.", "pt-BR") == "Uma frase nova que ninguém traduziu."


def test_codigos_valores_e_texto_ja_em_ingles_ficam_iguais():
    obj = {"codigo": "fonte_indisponivel", "estado": "final_com_cache", "cultura": "milho_2a_safra", "motivo": "possivel_sombra",
           "mensagem": "plantio mais cedo", "fonte": "NASA POWER", "origem_informada": "Cooperativa de Rio Verde", "valor": 67.34}
    t = i18n.traduzir_resposta(obj, "en")
    assert t == obj | {"mensagem": "earliest planting"}


def test_catalogo_sem_palavras_proibidas():
    exatos, modelos = i18n._catalogo()
    tudo = " ".join(list(exatos.values()) + [en for _, en, _ in modelos]).lower()
    assert not [p for p in PROIBIDAS if p in tudo]


def _sem_texto(obj, campo=None):
    """A resposta sem os campos de texto: o que sobra tem de ser idêntico nos dois idiomas (FR-009, SC-004)."""
    if isinstance(obj, dict):
        return {k: _sem_texto(v, k) for k, v in obj.items() if k not in i18n.CAMPOS_TEXTO and k not in ("idioma", "pedido")}
    if isinstance(obj, list):
        return [_sem_texto(v, campo) for v in obj]
    return obj


@pytest.fixture(scope="module")
def respostas():
    mp = pytest.MonkeyPatch()
    if (REF_SMAP / "rio_verde_go" / "serie.csv").exists():
        mp.setattr(umidade, "DIR_REFERENCIA", REF_SMAP)
    api = TestClient(app)
    pt = api.post("/api/contrato/calcular", json=PEDIDO)
    en = api.post("/api/contrato/calcular", json=PEDIDO | {"idioma": "en"})
    cab = api.post("/api/contrato/calcular", json=PEDIDO, headers={"Accept-Language": "en-US"})
    mp.undo()
    assert pt.status_code == en.status_code == cab.status_code == 200
    return pt, en, cab


def test_mesmo_calculo_em_pt_e_en(respostas):
    pt, en, _ = respostas
    a, b = pt.json(), en.json()
    assert a["idioma"] == "pt-BR" and b["idioma"] == "en"
    assert b["versoes"]["hash_pedido"] == a["versoes"]["hash_pedido"]
    assert _sem_texto(copy.deepcopy(b)) == _sem_texto(copy.deepcopy(a))
    assert [x["cultura"] for x in b["recomendacao"]["conteudo"]["alternativas"]] == \
           [x["cultura"] for x in a["recomendacao"]["conteudo"]["alternativas"]]


def test_resultado_de_referencia_todo_traduzido(respostas):
    pt, en, _ = respostas
    assert i18n.sem_traducao(pt.json()) == []  # SC-003: todo texto do caso de referência tem inglês no catálogo
    assert "(PT)" not in en.text
    assert en.headers["content-language"] == "en"


def test_accept_language_vale_sem_o_campo(respostas):
    _, en, cab = respostas
    assert cab.json()["idioma"] == "en"
    assert _sem_texto(cab.json()) == _sem_texto(en.json())


def test_erro_do_contrato_em_ingles():
    r = TestClient(app).post("/api/contrato/calcular", json=PEDIDO | {"versao_contrato": "2.0.0", "idioma": "en"})
    assert r.status_code == 422
    e = r.json()["erro"]
    assert e["codigo"] == "versao_incompativel" and not e["mensagem"].startswith("(PT)")


def test_pedido_1_1_0_sem_idioma_continua_aceito():
    r = TestClient(app).post("/api/contrato/calcular", json=PEDIDO | {"versao_contrato": "1.1.0"})
    assert r.status_code == 200 and r.json()["idioma"] == "pt-BR"


def test_outras_rotas_pelo_accept_language():
    api = TestClient(app)
    corpo = {"lat": -17.785278, "lon": -50.965, "cultura": "milho_2a_safra"}
    pt = api.post("/api/economia/margem", json=corpo)
    en = api.post("/api/economia/margem", json=corpo, headers={"Accept-Language": "en"})
    assert pt.status_code == en.status_code
    assert _sem_texto(pt.json()) == _sem_texto(en.json())


def test_catalogo_consistente():
    """Cada modelo tem os mesmos campos nos dois idiomas; nenhuma tradução vazia."""
    import json
    import re
    from pathlib import Path
    d = json.loads((Path(i18n.__file__).with_name("en.json")).read_text(encoding="utf-8"))
    assert all(v.strip() for v in d["exatos"].values())
    for pt, en in d["modelos"]:
        assert sorted(re.findall(r"\{(\w+)\}", pt)) == sorted(re.findall(r"\{(\w+)\}", en)), pt


def test_mensagens_de_erro_comuns_em_ingles():
    casos = {
        "Nenhum imóvel com esse número no CAR público.": "No property with that number in the public CAR.",
        "O WFS do SICAR não respondeu; usando a consulta guardada de 2026-11-14.":
            "The SICAR WFS did not respond; using the saved query from 2026-11-14.",
        "A estação INMET mais próxima (A025, Rio Verde) fica a 12.3 km. Acima de 50 km a comparação local de chuva perde validade.":
            "The nearest INMET station (A025, Rio Verde) is 12.3 km away. Beyond 50 km the local rainfall comparison loses validity.",
    }
    for pt, en in casos.items():
        assert i18n.traduzir(pt, "en") == en
