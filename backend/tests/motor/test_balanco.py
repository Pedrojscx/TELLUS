"""Caso calculado à mão do balanço (SC-001), com tolerância de 0,001 mm."""

import pytest

from tellus.motor import balanco, simulacao

# Cultura de 4 dias (1 dia por fase), Kc 0,5 / 1,0 / 0,5, p = 0,5, CAD = 20 mm; limites ISNA 0,7 e 0,55.
C = balanco.Cultura(fases=(1, 1, 1, 1), kc_ini=0.5, kc_med=1.0, kc_fim=0.5, p=0.5,
                    ky_fases=(0.4, 0.4, 1.5, 0.2), isna_limite_I=0.7, isna_limite_III=0.55)


def test_curva_kc():
    # fase I: 0,5; fase II (1 dia): sobe até 1,0; fase III: 1,0; fase IV (1 dia): desce até 0,5
    assert [balanco.kc_do_dia(C, d) for d in range(4)] == [0.5, 1.0, 1.0, 0.5]


def test_caso_a_mao():
    # ETo = 8 mm/dia; chuva = [0, 0, 0, 10]; Dr inicial = 0 (capacidade de campo).
    # Dia 1: Kc 0,5 → ETc 4; Dr0 = 0 ≤ RAW (10) → Ks 1 → ETa 4; Dr = 4.
    # Dia 2: Kc 1,0 → ETc 8; Dr 4 ≤ 10 → Ks 1 → ETa 8; Dr = 12.
    # Dia 3: Kc 1,0 → ETc 8; Dr 12 > 10 → Ks = (20 − 12)/(0,5·20) = 0,8 → ETa 6,4; Dr = 18,4.
    # Dia 4: Kc 0,5 → ETc 4; Dr 18,4 > 10 → Ks = 1,6/10 = 0,16 → ETa 0,64; Dr = 18,4 − 10 + 0,64 = 9,04.
    # ISNA por fase: 1; 1; 0,8; 0,16. Déficit: 0; 0; 1,6; 3,36 → 4,96 mm.
    # Perda FAO-33 multiplicativa: 1 − (1)(1)(1 − 1,5·0,2)(1 − 0,2·0,84) = 1 − 0,7·0,832 = 0,4176.
    # Falha severa: ISNA fase I = 1 > 0,7 e fase III = 0,8 > 0,55 → não.
    r = balanco.safra(0.0, [0, 0, 0, 10], [8, 8, 8, 8], C, 20.0)
    assert r["isna_fases"] == pytest.approx([1.0, 1.0, 0.8, 0.16], abs=1e-4)
    assert r["deficit_mm_fases"] == pytest.approx([0, 0, 1.6, 3.36], abs=1e-3)
    assert r["deficit_mm"] == pytest.approx(4.96, abs=1e-3)
    assert r["eta_mm"] == pytest.approx(19.04, abs=1e-3)
    assert r["dr_final"] == pytest.approx(9.04, abs=1e-3)
    assert r["perda_relativa"] == pytest.approx(0.4176, abs=1e-4)
    assert r["falha_severa"] is False


def test_drenagem_e_limite_de_murcha():
    dr, etc, eta, dren = balanco.passo(2.0, 15.0, 5.0, 1.0, 20.0, 0.5)
    assert (dr, dren) == (0.0, pytest.approx(8.0))  # 2 − 15 + 5 = −8 → drena 8
    dr, etc, eta, dren = balanco.passo(19.9, 0.0, 10.0, 1.0, 20.0, 0.5)
    assert dr == 20.0 and eta <= 0.1 + 1e-9  # não seca além da CAD


def _dias(n, chuva=0.0, eto=5.0, inicio="2010-01-01", buraco=None):
    import datetime as dt
    d0 = dt.date.fromisoformat(inicio)
    out = []
    for i in range(n):
        d = (d0 + dt.timedelta(days=i)).isoformat()
        out.append({"data": d, "chuva_mm": None if d == buraco else chuva, "eto_mm": eto})
    return out


def test_dia_ausente_interrompe_o_ano():
    r = simulacao.simular(_dias(40, buraco="2010-01-10"), C, 20.0, "01-05", "01-07", 0.3, 1.0)
    assert r["anos_validos"] == 0 and "2010-01-10" in r["anos_excluidos"][0]["motivo"]


def test_pousio_seca_mais_que_palhada():
    pousio = simulacao.simular(_dias(40), C, 20.0, "01-01", "01-11", 0.30, 1.0)
    palhada = simulacao.simular(_dias(40), C, 20.0, "01-01", "01-11", 0.15, 1.0)
    assert pousio["por_ano"][0]["agua_no_plantio_frac"] < palhada["por_ano"][0]["agua_no_plantio_frac"]


def test_deterministico():
    a = simulacao.simular(_dias(40, chuva=1.0), C, 20.0, "01-01", "01-03", 0.15, 0.8)
    b = simulacao.simular(_dias(40, chuva=1.0), C, 20.0, "01-01", "01-03", 0.15, 0.8)
    assert a == b
