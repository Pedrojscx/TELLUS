"""#53/#95: SMAP é só contexto regional. Nenhum texto o chama de medição da lavoura ou de previsão,
e nenhum módulo de cálculo o importa.

O motor de recomendação (spec 008) ainda não existe. A comparação "mesmo cálculo com e sem SMAP"
fica para quando ele existir. Hoje o teste é estrutural: nenhum módulo fora de `tellus.umidade`
(exceto a rota e o app) importa umidade, e a resposta não tem campo de recomendação.
"""

import ast
from pathlib import Path

import pytest

from tellus.umidade import regras, servico

from .conftest import LAT, LON

SRC = Path(__file__).resolve().parents[2] / "src" / "tellus"
PERMITIDOS = {SRC / "api" / "umidade.py", SRC / "api" / "app.py"}
PROIBIDOS_NO_TEXTO = ("previsão", "previsao", "vai chover", "medição da fazenda", "medição da lavoura", "produtividade")


def _imports(caminho: Path) -> set[str]:
    nomes = set()
    for no in ast.walk(ast.parse(caminho.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            nomes |= {a.name for a in no.names}
        elif isinstance(no, ast.ImportFrom):
            base = no.module or ""
            nomes.add(base)
            nomes |= {f"{base}.{a.name}" for a in no.names}
            if no.level and caminho.parent.name == "umidade":
                nomes.add("tellus.umidade")
    return nomes


def test_nenhum_modulo_de_calculo_importa_umidade():
    culpados = []
    for p in SRC.rglob("*.py"):
        if "umidade" in p.relative_to(SRC).parts or p in PERMITIDOS:
            continue
        if any(n == "tellus.umidade" or n.startswith("tellus.umidade.") for n in _imports(p)):
            culpados.append(str(p.relative_to(SRC)))
    assert culpados == []


def test_umidade_nao_depende_de_calculo_nem_de_clima():
    for p in (SRC / "umidade").glob("*.py"):
        de_tellus = {n for n in _imports(p) if n.startswith("tellus.") and not n.startswith("tellus.umidade")}
        assert all(n.startswith("tellus.localizacao") for n in de_tellus), (p.name, de_tellus)


def _cenarios(cache_sintetico, tmp_path):
    yield servico.contexto(LAT, LON, dir_cache=cache_sintetico)
    yield servico.contexto(LAT, LON, inicio="2025-01-09", fim="2025-01-15", dir_cache=cache_sintetico)
    yield servico.contexto(LAT, LON, variante="PM", data="2025-01-11", dir_cache=cache_sintetico)
    yield servico.contexto(87.0, 0.0, dir_cache=tmp_path)
    yield servico.produtos()


def test_varredura_de_texto_nas_respostas(cache_sintetico, tmp_path):
    for resp in _cenarios(cache_sintetico, tmp_path):
        textos = " | ".join(regras.textos(resp)).lower()
        for termo in PROIBIDOS_NO_TEXTO:
            assert termo not in textos, termo
        assert regras.termos_proibidos(resp) == []


def test_resposta_sem_campo_de_recomendacao_ou_produtividade(cache_sintetico, tmp_path):
    for resp in _cenarios(cache_sintetico, tmp_path):
        assert not [k for k in regras.chaves(resp) if k in regras.CHAVES_PROIBIDAS]


def test_contexto_sempre_regional_e_opcional(cache_sintetico):
    r = servico.contexto(LAT, LON, dir_cache=cache_sintetico)
    assert r["natureza"] == "contexto_regional" and r["opcional"] is True
    assert "não entra em nenhum cálculo" in r["uso"]
    assert all(i["natureza"] == "contexto_regional" for i in r["itens"])


def test_textos_do_codigo_fonte_da_umidade():
    """Strings literais do módulo e da rota (o que a tela pode receber), exceto a lista de termos."""
    for p in [*(SRC / "umidade").glob("*.py"), SRC / "api" / "umidade.py"]:
        for no in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Constant) and isinstance(no.value, str) and no.value not in regras.TERMOS_PROIBIDOS \
                    and no.value not in regras.CHAVES_PROIBIDAS:
                baixo = no.value.lower()
                assert not any(t in baixo for t in PROIBIDOS_NO_TEXTO), (p.name, no.value[:80])


def test_guarda_do_contrato_barra_violacao():
    with pytest.raises(AssertionError, match="contrato"):
        servico._garantir_contrato({"itens": [{"estado": "disponivel"}], "produtividade": 1})
