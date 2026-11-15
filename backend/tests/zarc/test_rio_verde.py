"""SC-001: Rio Verde-GO confere com o relatório SISZARC (valores registrados em 14/11 e XLS salvo)."""

import glob
from pathlib import Path

import pytest

from tellus.zarc import regras, servico, siszarc

RV = "5218805"
RAIZ = Path(__file__).resolve().parents[3]


def janela(cultura, grupo, solo):
    cal = servico.calendario(RV, cultura, grupo, solo)
    g = cal["grupos"][0]
    return {j["decendio"]: j["risco_zarc_pct"] for j in g["solos"][0]["janela"]}, g["proveniencia"]


def test_milho_grupo_i_como_no_registro():
    # Conferência de 14/11 (spec 004): dec 1–3 = 20% em todos os solos; dec 4: AD1 40, AD2–AD3 30, AD4–AD6 20;
    # dec 5: AD4 40, AD5 30, AD6 20; dec 6: só AD6 (30%).
    esperado = {
        "AD1": {1: 20, 2: 20, 3: 20, 4: 40},
        "AD2": {1: 20, 2: 20, 3: 20, 4: 30},
        "AD3": {1: 20, 2: 20, 3: 20, 4: 30},
        "AD4": {1: 20, 2: 20, 3: 20, 4: 20, 5: 40},
        "AD5": {1: 20, 2: 20, 3: 20, 4: 20, 5: 30},
        "AD6": {1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 30},
    }
    for solo, jan in esperado.items():
        obtido, prov = janela("milho_2a_safra", "GRUPO I", solo)
        assert obtido == jan, solo
    assert prov["portaria"] == "322" and prov["data_portaria"] == "2026-07-30" and prov["vigente"]


def test_sorgo_grupo_i_como_no_registro():
    # arenoso (tipo 1) até dec 6 com 40%; média (tipo 2) até dec 7 com 30%; argiloso (tipo 3) 20% até dec 8, 30% no 9
    j1, _ = janela("sorgo_granifero_2a_safra", "GRUPO I", "1")
    j2, _ = janela("sorgo_granifero_2a_safra", "GRUPO I", "2")
    j3, prov = janela("sorgo_granifero_2a_safra", "GRUPO I", "3")
    assert max(j1) == 6 and j1[6] == 40
    assert max(j2) == 7 and j2[7] == 30
    assert all(j3[d] == 20 for d in range(1, 9)) and j3[9] == 30 and max(j3) == 9
    assert prov["portaria"] == "273"


def test_milho_grupo_ii_mais_curto():
    j1, _ = janela("milho_2a_safra", "GRUPO I", "AD6")
    j2, _ = janela("milho_2a_safra", "GRUPO II", "AD6")
    assert max(j2) <= max(j1)


def test_referencia_confere_com_xls_salvo():
    arquivos = glob.glob(str(RAIZ / "data" / "raw" / "zarc" / "siszarc" / "*_GO_*.xls"))
    if not arquivos:
        pytest.skip("XLS bruto do SISZARC não está nesta máquina (data/raw fica fora do Git)")
    for arq in arquivos:
        for linha in siszarc.ler_relatorio(Path(arq).read_bytes()):
            if linha["municipio"] != "Rio Verde":
                continue
            chave = next(k for k, c in servico.CULTURAS["culturas"].items() if c["nome"].split()[0] in linha["cultura"]
                         and ("Braqui" in linha["cultura"]) == ("braquiaria" in k)
                         and ("Sorgo" in linha["cultura"]) == ("sorgo" in k)
                         and ("2ª" in linha["cultura"] or "2" in linha["cultura"]) == ("2a" in k))
            obtido, _ = janela(chave, linha["grupo"], linha["solo"])
            assert obtido == {i + 1: r for i, r in enumerate(linha["riscos"]) if r}, (arq, linha["grupo"], linha["solo"])
