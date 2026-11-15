"""Chuva ponderada por área (#35, spec 003 FR-001/FR-002): geometria confirmada × células IMERG de 0,1°.

Os caches daqui são SINTÉTICOS (tmp_path); o caso real de Rio Verde está em test_rio_verde_area.py.
"""

import csv
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import clima as rotas
from tellus.car import regras as regras_car
from tellus.clima import imerg, servico
from tellus.clima.servico import ErroClima

from .conftest import LAT, LON

CEL_A = imerg.CelulaImerg.do_ponto(LAT, LON)  # centro (−17,75; −50,95): lon de −51,0 a −50,9
CEL_B = imerg.CelulaImerg(CEL_A.i_lat, CEL_A.i_lon + 1)  # vizinha a leste: lon de −50,9 a −50,8


def _ret(lon0, lon1, lat0, lat1) -> dict:
    return {"type": "Polygon", "coordinates": [[[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]]}


def _id(g: dict) -> str:
    return regras_car.id_geometria(g, 6)


def _gravar_celula(dir_cache, cel, linhas):
    p = imerg.arquivo_cache(dir_cache, cel)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(imerg.CAMPOS)
        for d, v, c, s in linhas:
            w.writerow([d, v, c, s, "2026-11-14"])


@pytest.fixture
def cache_duas(cache_falso):
    """Célula A do conftest (3,5 / sem_dado / 0,0 / não publicado) + vizinha B, SINTÉTICA."""
    _gravar_celula(cache_falso, CEL_B, [
        ("2025-09-28", "20.0000", "48", "ok"),
        ("2025-09-29", "5.0000", "48", "ok"),   # A sem dado neste dia
        ("2025-09-30", "", "0", "sem_dado"),     # B sem dado neste dia
        ("2025-10-01", "", "", "nao_publicado"),
    ])
    # o centro desta área (−17,75; −50,92) cai noutra célula POWER (−50,625): copia a série sintética
    from tellus.clima import power
    origem, destino = power.arquivo_cache(cache_falso, LAT, LON), power.arquivo_cache(cache_falso, -17.75, -50.92)
    destino.write_bytes(origem.read_bytes())
    destino.with_suffix(".json.meta.json").write_bytes(origem.with_suffix(".json.meta.json").read_bytes())
    return cache_falso


# 70% em A e 30% em B: lon de −50,97 a −50,87 (0,1°), toda a faixa dentro da mesma linha de células
G_DUAS = _ret(-50.97, -50.87, -17.78, -17.72)


def test_caso_a_mao_duas_celulas(cache_duas):
    """Pesos: na longitude, 0,07° de 0,10° caem em A (−50,97 a −50,90) e 0,03° em B (−50,90 a −50,87).

    Com a amostragem de 0,005°: 20 colunas, 14 em A e 6 em B → 0,7 e 0,3 (as linhas são todas iguais).
    2025-09-28: 0,7 × 3,5 + 0,3 × 20,0 = 2,45 + 6,00 = 8,45 mm
    2025-09-29: A sem dado → dia indisponível (não vira 5,0 nem 0,3 × 5,0)
    2025-09-30: B sem dado → dia indisponível (não vira 0,0)
    """
    s = servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_duas)
    loc = s["proveniencia"]["chuva"]["localizacao"]
    pesos = {c["chave"]: c["peso"] for c in loc["celulas"]}
    assert pesos == {CEL_A.chave: 0.7, CEL_B.chave: 0.3}
    assert loc["soma_pesos"] == 1.0 and loc["tipo"] == "geometria" and loc["id_geometria"] == _id(G_DUAS)
    assert [d["chuva_mm"] for d in s["dias"]] == [8.45, None, None]


def test_celula_sem_dado_deixa_o_dia_indisponivel_sem_renormalizar(cache_duas):
    s = servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_duas)
    d29, d30 = s["dias"][1], s["dias"][2]
    assert d29["chuva_mm"] is None and d29["celulas_sem_dado"] == [CEL_A.chave]
    assert d30["chuva_mm"] is None and d30["celulas_sem_dado"] == [CEL_B.chave]
    aviso = next(a for a in s["avisos"] if a["codigo"] == "dia_indisponivel_celula")
    assert "2025-09-29" in aviso["mensagem"] and "não é recalculada" in aviso["mensagem"]
    q = s["proveniencia"]["chuva"]["qualidade"]
    assert (q["dias_validos"], q["dias_ausentes"], q["dias_nao_publicados"]) == (1, 2, 1)
    por_cel = {c["chave"]: c["qualidade"] for c in s["proveniencia"]["chuva"]["localizacao"]["celulas"]}
    assert por_cel[CEL_A.chave]["dias_sem_dado"] == 1 and por_cel[CEL_B.chave]["dias_sem_dado"] == 1


def test_geometria_dentro_de_uma_celula_igual_ao_ponto(cache_falso):
    g = _ret(-50.98, -50.95, -17.79, -17.76)  # inteira em A, a mesma célula do ponto
    area = servico.serie(geometria=g, id_geometria=_id(g), dir_cache=cache_falso)
    ponto = servico.serie(LAT, LON, dir_cache=cache_falso)
    assert area["dias"] == ponto["dias"]
    assert [c["peso"] for c in area["proveniencia"]["chuva"]["localizacao"]["celulas"]] == [1.0]
    assert area["proveniencia"]["chuva"]["qualidade"] == ponto["proveniencia"]["chuva"]["qualidade"]


def test_ponto_continua_com_uma_celula_peso_1(cache_falso):
    """Ponto: a mesma proveniência de antes da #35 (o contrato 011 grava a resposta do ponto)."""
    s = servico.serie(LAT, LON, dir_cache=cache_falso)
    loc = s["proveniencia"]["chuva"]["localizacao"]
    assert loc == {"celulas": [{"centro_lat": -17.75, "centro_lon": -50.95, "peso": 1.0}], "distancia_km": loc["distancia_km"]}
    assert s["proveniencia"]["chuva"]["periodo"] == {"inicio": "2025-09-28", "fim": "2025-09-30"}
    assert "celulas_sem_dado" not in s["dias"][1]  # ponto: dia sem dado continua só None


def test_proveniencia_tem_versao_periodo_utc_celula_e_qualidade(cache_duas):
    p = servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_duas)["proveniencia"]["chuva"]
    assert p["versao"] == "GPM_3IMERGDF V07B"
    assert p["periodo"] == {"inicio": "2025-09-28", "fim": "2025-09-30", "fuso": "UTC (dia IMERG de 00:00 a 23:59:59 UTC)"}
    for c in p["localizacao"]["celulas"]:
        assert c["limites"]["lat"] == [-17.8, -17.7]
        assert c["qualidade"]["contagem_media"] == 48.0 and c["origem_dados"] == "cache" and c["obtido_em"] == "2026-11-14"


def test_celula_sem_cache_e_erro_que_nomeia_a_celula(cache_falso):
    with pytest.raises(ErroClima) as e:
        servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_falso)
    assert e.value.codigo == "sem_cache" and "IMERG" in e.value.origem
    assert CEL_B.chave in e.value.mensagem


def test_geometria_precisa_estar_confirmada(cache_duas):
    with pytest.raises(ErroClima) as e:
        servico.serie(geometria=G_DUAS, id_geometria="outro", dir_cache=cache_duas)
    assert e.value.codigo == "geometria_nao_confirmada" and e.value.status == 422


def test_determinismo_area(cache_duas):
    a = servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_duas)
    b = servico.serie(geometria=G_DUAS, id_geometria=_id(G_DUAS), dir_cache=cache_duas)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_rota_post_serie_e_resumo(cache_duas, monkeypatch):
    monkeypatch.setattr(servico, "DIR_CACHE", cache_duas)
    app = FastAPI()
    app.include_router(rotas.router)
    cli = TestClient(app)
    r = cli.post("/api/clima/serie", json={"geometria": G_DUAS, "id_geometria": _id(G_DUAS)})
    assert r.status_code == 200 and [d["chuva_mm"] for d in r.json()["dias"]] == [8.45, None, None]
    r = cli.post("/api/clima/resumo", json={"geometria": G_DUAS, "id_geometria": _id(G_DUAS)})
    assert r.status_code == 200 and r.json()["local"]["tipo"] == "geometria"
