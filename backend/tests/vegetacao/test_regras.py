"""Motor puro de vegetação: casos com contas à mão (Princípio VI)."""

import datetime as dt
import socket

import pytest

from tellus.vegetacao import regras, servico

GRADE = servico.GRADE
NDVI = servico.PRODUTOS["MOD13Q1"]["indices"]["ndvi"]
REGRA_MODIS = {"pixel_reliability_aceitos": [0]}
REGRA_HLS = {"fmask_bits_rejeitados": [1, 2, 3, 4]}
BANDAS = servico.PRODUTOS["HLS"]["bandas"]


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    def bloqueado(*a, **k):
        raise RuntimeError("rede bloqueada no teste do motor")
    monkeypatch.setattr(socket, "socket", bloqueado)


def test_pixel_senoidal_rio_verde_conta_a_mao():
    """Rio Verde-GO (−17,785278; −50,965).

    φ = −0,3104117 rad; λ = −0,8895071 rad; cos φ = 0,9522079
    x = R·λ·cos φ = 6 371 007,181 × −0,8895071 × 0,9522079 = −5 396 215,4 m
    y = R·φ = 6 371 007,181 × −0,3104117 = −1 977 634,9 m
    dx = x + 20 015 109,354 = 14 618 894,0 → dx / 1 111 950,52 = 13,147 → h = 13
    dy = 10 007 554,677 − y = 11 985 189,6 → dy / 1 111 950,52 = 10,779 → v = 10
    pixel = 1 111 950,52 / 4800 = 231,656 m
    coluna = (14 618 894,0 − 13 × 1 111 950,52) / 231,656 = 705,95 → 705
    linha  = (11 985 189,6 − 10 × 1 111 950,52) / 231,656 = 3736,93 → 3736
    """
    x, y = regras.xy_senoidal(-17.785278, -50.965, GRADE)
    assert x == pytest.approx(-5396215.4, abs=0.5)
    assert y == pytest.approx(-1977634.9, abs=0.5)
    assert regras.pixel_senoidal(-17.785278, -50.965, GRADE) == "h13v10.l3736.c0705"


def test_pesos_ponto_e_poligono_somam_um():
    assert regras.pesos_pixels({"type": "Point", "coordinates": [-50.965, -17.785278]}, GRADE) == {"h13v10.l3736.c0705": 1.0}
    pol = {"type": "Polygon", "coordinates": [[[-50.968, -17.788], [-50.962, -17.788], [-50.962, -17.782],
                                               [-50.968, -17.782], [-50.968, -17.788]]]}
    pesos = regras.pesos_pixels(pol, GRADE)
    assert len(pesos) > 1
    assert sum(pesos.values()) == pytest.approx(1.0)


def test_calendario_modis_terra_e_aqua():
    terra = regras.calendario(dt.date(2024, 1, 1), dt.date(2024, 12, 31), 1, 16)
    aqua = regras.calendario(dt.date(2024, 1, 1), dt.date(2024, 12, 31), 9, 16)
    assert len(terra) == 23 and terra[0] == dt.date(2024, 1, 1) and terra[-1] == dt.date(2024, 12, 18)  # DOY 353
    assert aqua[0] == dt.date(2024, 1, 9)
    assert regras.fim_composicao(dt.date(2024, 12, 18), 16) == dt.date(2024, 12, 31)  # última do ano encurta
    assert regras.fim_composicao(dt.date(2024, 1, 1), 16) == dt.date(2024, 1, 16)


@pytest.mark.parametrize(
    ("bruto", "rel", "esperado"),
    [
        (7342, 0, (0.7342, None)),           # 7342 × 0,0001
        (7342, 3, (None, "nuvem")),
        (7342, 1, (None, "dado_marginal")),  # marginal é lacuna na hipótese
        (7342, 2, (None, "neve_gelo")),
        (-3000, -1, (None, "sem_dado")),
        (12000, 0, (None, "fora_da_faixa_valida")),
        (None, 0, (None, "sem_dado")),
    ],
)
def test_valor_modis(bruto, rel, esperado):
    assert regras.valor_modis(bruto, rel, NDVI, REGRA_MODIS) == esperado


def test_regra_modis_e_parametro():
    assert regras.valor_modis(7342, 1, NDVI, {"pixel_reliability_aceitos": [0, 1]}) == (0.7342, None)


def test_hls_ndvi_e_evi_conta_a_mao():
    """vermelho 600 → 0,06; nir 3600 → 0,36; azul 400 → 0,04.

    NDVI = (0,36 − 0,06) / (0,36 + 0,06) = 0,30 / 0,42 = 0,714286 → 0,7143
    EVI = 2,5 × 0,30 / (0,36 + 0,36 − 0,30 + 1) = 0,75 / 1,42 = 0,528169 → 0,5282
    """
    b = {"azul": 400, "vermelho": 600, "nir": 3600}
    assert regras.valor_hls(b, 0, "ndvi", BANDAS, REGRA_HLS) == (0.7143, None)
    assert regras.valor_hls(b, 0, "evi", BANDAS, REGRA_HLS) == (0.5282, None)
    assert regras.valor_hls(b, 0b10, "ndvi", BANDAS, REGRA_HLS) == (None, "nuvem")
    assert regras.valor_hls(b, 0b1000, "ndvi", BANDAS, REGRA_HLS) == (None, "sombra_nuvem")
    assert regras.valor_hls(b, 0b100000, "ndvi", BANDAS, REGRA_HLS) == (0.7143, None)  # água não rejeitada
    assert regras.valor_hls(b | {"nir": -9999}, 0, "ndvi", BANDAS, REGRA_HLS) == (None, "sem_dado")
    assert regras.bandeiras_fmask(0b1010) == ["nuvem", "sombra_nuvem"]


def test_agregar_area_sem_preenchimento():
    pesos = {"a": 0.5, "b": 0.25, "c": 0.25}
    ok = {"a": (0.8, None), "b": (0.4, None), "c": (0.6, None)}
    # 0,5×0,8 + 0,25×0,4 + 0,25×0,6 = 0,40 + 0,10 + 0,15 = 0,65
    assert regras.agregar_area(ok, pesos, 1.0)["valor"] == 0.65
    um_ruim = ok | {"b": (None, "nuvem")}
    r = regras.agregar_area(um_ruim, pesos, 1.0)
    assert r["valor"] is None and r["motivo"] == "nuvem" and r["cobertura_valida"] == 0.75
    # com cobertura mínima 0,75 (parâmetro): média dos válidos = (0,40 + 0,15) / 0,75 = 0,7333
    assert regras.agregar_area(um_ruim, pesos, 0.75)["valor"] == 0.7333
    falta = regras.agregar_area({"a": (0.8, None)}, pesos, 1.0)
    assert falta["valor"] is None and falta["motivo"] == "ausente_no_cache"


def test_sazonalidade_ignora_lacunas():
    obs = [(dt.date(2023, 1, 1), 0.8), (dt.date(2024, 1, 1), None), (dt.date(2024, 1, 17), 0.6), (dt.date(2023, 7, 1), None)]
    jan, jul = regras.sazonalidade_mensal(obs)
    assert jan == {"mes": 1, "media": 0.7, "minimo": 0.6, "maximo": 0.8, "n_validas": 2, "n_composicoes": 3}
    assert jul == {"mes": 7, "media": None, "minimo": None, "maximo": None, "n_validas": 0, "n_composicoes": 1}


def test_marginal_consulta_vi_quality():
    """Tabela 4: rank 1 'look at other QA'. 2116 = 0b1000_0100_0100: MODLAND 00, sem bits 8/10/14/15."""
    regra = {"pixel_reliability_aceitos": [0], "pixel_reliability_condicionais": [1],
             "condicional_modland_aceitos": [0, 1], "condicional_bits_vi_quality_rejeitados": [8, 10, 14, 15]}
    assert regras.valor_modis(5000, 1, NDVI, regra, 2116) == (0.5, None)
    assert regras.valor_modis(5000, 1, NDVI, regra, 2116 | 1 << 8) == (None, "nuvem_adjacente")
    assert regras.valor_modis(5000, 1, NDVI, regra, 2116 | 1 << 15) == (None, "possivel_sombra")
    assert regras.valor_modis(5000, 1, NDVI, regra, 2116 | 0b10) == (None, "dado_marginal")  # MODLAND 10: nuvem
    assert regras.valor_modis(5000, 1, NDVI, regra, None) == (None, "dado_marginal")
    assert regras.valor_modis(5000, 3, NDVI, regra, 2116) == (None, "nuvem")
