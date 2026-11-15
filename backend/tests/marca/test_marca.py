"""Spec 013 (#106, #105): contraste da paleta, selos com texto, sem elemento de terceiros na identidade."""

import runpy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]


def test_contraste_aa_em_todos_os_pares():
    mod = runpy.run_path(str(RAIZ / "scripts" / "verificar_contraste.py"))
    c = mod["cores"]()
    for nome, frente, fundo in mod["pares"](c):
        assert mod["contraste"](frente, fundo) >= 4.5, nome


def test_selo_tem_texto_para_todo_estado():
    selo = (RAIZ / "frontend" / "src" / "components" / "marca" / "Selo.astro").read_text(encoding="utf-8")
    for rotulo in ('fonte: "Fonte"', 'hipotese: "Hipótese"', 'aviso: "Aviso"', 'erro: "Erro"'):
        assert rotulo in selo
    assert 'role={tipo === "erro"' in selo


def test_icone_proprio_sem_logo_do_astro():
    fav = (RAIZ / "frontend" / "public" / "favicon.svg").read_text(encoding="utf-8")
    assert "TELLUS" in fav and "astro" not in fav.lower()
    assert not (RAIZ / "frontend" / "public" / "favicon.ico").exists()


def test_guia_sem_elemento_de_terceiros_pendente():
    guia = (RAIZ / "docs" / "marca" / "GUIA_DE_MARCA.md").read_text(encoding="utf-8")
    assert "Elementos de terceiros incorporados à identidade: nenhum" in guia
