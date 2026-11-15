"""Regras puras: grade EASE-Grid 2.0 e contrato do item.

Valores esperados obtidos com pyproj (EPSG:6933) em 2026-11-15. Ver referencias/umidade/FONTE.md.
"""

import pytest

from tellus.umidade import regras

M09, M36 = (3856, 1624), (964, 406)


def test_projecao_confere_com_pyproj():
    x, y = regras.ease2_xy(-17.785278, -50.965)
    assert x == pytest.approx(-4917423.272986941, abs=1e-6) and y == pytest.approx(-2233594.513642269, abs=1e-6)
    assert regras.ease2_xy(84, 179) == pytest.approx((17271044.164910477, 7301649.868311009), abs=1e-6)
    lat, lon = regras.ease2_latlon(x, y)
    assert (lat, lon) == pytest.approx((-17.785278, -50.965), abs=1e-7)


def test_tamanho_das_celulas():
    assert regras.tamanho_celula_m(964) == pytest.approx(36032.22, abs=0.01)  # guia SPL3SMP V009
    assert regras.tamanho_celula_m(3856) == pytest.approx(9008.055, abs=0.001)


def test_celula_de_rio_verde():
    assert regras.celula_ease2(-17.785278, -50.965, *M09) == (1059, 1382)
    assert regras.centro_celula(1059, 1382, *M09) == (-17.75156, -50.92842)
    assert regras.celula_ease2(-17.785278, -50.965, *M36) == (264, 345)
    assert regras.centro_celula(264, 345, *M36) == (-17.64053, -50.9751)


def test_bordas_da_grade():
    assert regras.celula_ease2(86.0, 0.0, *M09) is None
    assert regras.celula_ease2(-85.0, 0.0, *M09) == (1623, 1928)
    assert regras.celula_ease2(0.0, 180.0, *M09) == (812, 3855)
    assert regras.celula_ease2(0.0, -180.0, *M09) == (812, 0)


def test_qualidade_bit0():
    assert regras.qualidade_l3(0, 65534)["recomendada"] is True
    assert regras.qualidade_l3(1, 65534)["recomendada"] is False
    assert regras.qualidade_l3(8, 65534)["recomendada"] is True  # só o bit 0 decide
    assert regras.qualidade_l3(65534, 65534)["situacao"] == "desconhecido"
    assert regras.qualidade_l3(None, 65534)["recomendada"] is None


def test_item_indisponivel_nao_aceita_valor():
    base = dict(produto={}, versao={}, celula={}, periodo={}, unidade={}, qualidade={}, resolucao={}, aviso={})
    with pytest.raises(ValueError):
        regras.item_contexto(estado="indisponivel", valor=0.2, motivo="x", **base)
    with pytest.raises(ValueError):
        regras.item_contexto(estado="indisponivel", valor=None, motivo=None, **base)


def test_metadado_sem_valor_so_pode_ser_desconhecido():
    with pytest.raises(ValueError):
        regras.metadado(None, regras.CONFIRMADO_NO_ARQUIVO)
    assert regras.metadado(None, regras.DESCONHECIDO)["situacao"] == "desconhecido"
