import json

import pytest

from tellus.clima import servico

LAT, LON = -17.785278, -50.965

CAMPOS_PROV = ["fonte", "versao", "periodo", "unidade", "localizacao", "qualidade", "resolucao", "aviso_escala", "obtido_em", "url"]


def test_serie_basica(cache_falso):
    s = servico.serie(LAT, LON, dir_cache=cache_falso)
    assert [d["data"] for d in s["dias"]] == ["2025-09-28", "2025-09-29", "2025-09-30"]
    assert [d["chuva_mm"] for d in s["dias"]] == [3.5, None, 0.0]  # sem_dado vira None, nunca zero
    assert s["dias"][1]["radiacao_mj_m2"] is None  # -999 do POWER vira None
    assert s["ultimo_dia_publicado_imerg"] == "2025-09-30"


def test_chuva_power_nunca_entra(cache_falso):
    s = servico.serie(LAT, LON, dir_cache=cache_falso)
    assert all(d["chuva_mm"] != 99.0 for d in s["dias"])
    assert all("PRECTOTCORR" not in d and "power_chuva_mm" not in d for d in s["dias"])


def test_rastreabilidade_completa(cache_falso):
    s = servico.serie(LAT, LON, dir_cache=cache_falso)
    for chave in ("chuva", "power"):
        prov = s["proveniencia"][chave]
        for campo in CAMPOS_PROV:
            assert prov.get(campo) not in (None, "", {}), f"{chave}.{campo} vazio"
    assert s["proveniencia"]["chuva"]["qualidade"] == {
        "dias_validos": 2, "dias_ausentes": 1, "dias_nao_publicados": 1, "contagem_media": 48.0,
    }


def test_lacuna_imerg_avisada(cache_falso):
    s = servico.serie(LAT, LON, fim="2025-12-31", dir_cache=cache_falso)
    assert s["dias"][-1]["data"] == "2025-09-30"
    assert "lacuna_imerg" in {a["codigo"] for a in s["avisos"]}


def test_reprodutibilidade(cache_falso):
    a = servico.serie(LAT, LON, dir_cache=cache_falso)
    b = servico.serie(LAT, LON, dir_cache=cache_falso)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_sem_cache_cita_a_fonte(tmp_path):
    with pytest.raises(servico.ErroClima) as e:
        servico.serie(-3.1, -60.0, dir_cache=tmp_path)  # Manaus: nem cache nem referência
    assert e.value.codigo == "sem_cache"
    assert "IMERG" in e.value.origem and "POWER" in e.value.origem
