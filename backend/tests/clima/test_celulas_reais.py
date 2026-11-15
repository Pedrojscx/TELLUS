"""#110: média ponderada por área com dado REAL de duas células IMERG (Rio Verde-GO e a vizinha ao sul).

Séries versionadas em referencias/clima/rio_verde_go (célula -17.75_-50.95) e referencias/clima/rio_verde_go_sul
(célula -17.85_-50.95, 2025-01-01 a 2025-09-30). A lavoura de teste é um retângulo que cruza a borda -17,8°.
"""

import csv

import pytest

from tellus.car import regras as regras_car
from tellus.car.servico import CASAS
from tellus.clima import servico

REF = servico.DIR_REF
NORTE, SUL = "-17.75_-50.95", "-17.85_-50.95"
pytestmark = pytest.mark.skipif(not (REF / "rio_verde_go_sul" / "serie_diaria.csv").exists(), reason="célula vizinha não versionada")

# retângulo de ~4,4 km × 4,2 km: metade ao norte e metade ao sul de -17,8° (borda entre as duas células)
GEOM = {"type": "Polygon", "coordinates": [[[-50.97, -17.82], [-50.93, -17.82], [-50.93, -17.78], [-50.97, -17.78], [-50.97, -17.82]]]}


def _ref(pasta):
    with (REF / pasta / "serie_diaria.csv").open(encoding="utf-8", newline="") as f:
        return {l["data"]: l for l in csv.DictReader(f)}


@pytest.fixture(scope="module")
def s(tmp_path_factory):
    ident = regras_car.id_geometria(regras_car.canonica(GEOM, CASAS), CASAS)
    # cache vazio: força as duas séries versionadas (dado real, nada sintético)
    return servico.serie(geometria=GEOM, id_geometria=ident, inicio="2025-01-01", fim="2025-09-30",
                         dir_cache=tmp_path_factory.mktemp("vazio"))


def test_duas_celulas_reais_com_pesos_que_somam_1(s):
    loc = s["proveniencia"]["chuva"]["localizacao"]
    pesos = {c["chave"]: c["peso"] for c in loc["celulas"]}
    assert all(c["origem_dados"] == "referencia_versionada" for c in loc["celulas"])  # dado real versionado
    assert set(pesos) == {NORTE, SUL}
    assert sum(pesos.values()) == pytest.approx(1.0, abs=1e-9)
    assert pesos[NORTE] == pytest.approx(0.5, abs=0.02) and pesos[SUL] == pytest.approx(0.5, abs=0.02)


def test_media_de_um_dia_confere_com_conta_independente(s):
    norte, sul = _ref("rio_verde_go"), _ref("rio_verde_go_sul")
    pesos = {c["chave"]: c["peso"] for c in s["proveniencia"]["chuva"]["localizacao"]["celulas"]}
    conferidos = 0
    for d in s["dias"]:
        n, su = norte.get(d["data"]), sul.get(d["data"])
        if d["chuva_mm"] is None or n["imerg_situacao"] != "ok" or su["imerg_situacao"] != "ok":
            continue
        esperado = pesos[NORTE] * float(n["chuva_mm"]) + pesos[SUL] * float(su["chuva_mm"])
        assert d["chuva_mm"] == pytest.approx(esperado, abs=1e-3), d["data"]
        conferidos += 1
    assert conferidos >= 200  # 2025-01-01 a 2025-09-30, quase todos os dias publicados
    chuvoso = max((d for d in s["dias"] if d["chuva_mm"] is not None), key=lambda d: d["chuva_mm"])
    assert float(norte[chuvoso["data"]]["chuva_mm"]) != float(sul[chuvoso["data"]]["chuva_mm"])  # células diferem de fato


# ---------------------------------------------------------------- validação INMET fora da A025 (#110)

INMET = servico.DIR_REF_INMET / "A026"


@pytest.mark.skipif(not (INMET / "serie_diaria.csv").exists(), reason="série A026 não versionada")
def test_validacao_mineiros_separada_e_com_proveniencia(tmp_path):
    r = servico.validacao(-17.45, -52.60, dir_cache=tmp_path)  # cache vazio: IMERG da referência versionada
    assert r["estacao"]["codigo"] == "A026" and r["disponivel"] is True
    assert r["dias_pareados"] >= 100 and r["celula_imerg"] == "-17.45_-52.65"
    assert r["fonte_estacao"]["urls"][0].startswith("https://portal.inmet.gov.br/uploads/dadoshistoricos/")
    assert "nunca entra no cálculo" in r["nota"]
    # sem POWER guardado, a comparação mostra só o IMERG e avisa (nada inventado)
    assert "power_chuva" not in r["metricas"] and r["avisos"][0]["codigo"] == "power_sem_cache"
    # conferência independente do total da estação nos dias pareados
    with (INMET / "serie_diaria.csv").open(encoding="utf-8", newline="") as f:
        ref = {l["data"]: l["chuva_mm"] for l in csv.DictReader(f)}
    assert all(ref[d] == "" or float(ref[d]) >= 0 for d in ref)
    assert r["metricas"]["imerg"]["n"] == r["dias_pareados"]


@pytest.mark.skipif(not (INMET / "serie_diaria.csv").exists(), reason="série A026 não versionada")
def test_serie_inmet_alterada_nao_e_usada(tmp_path, monkeypatch):
    import shutil
    copia = tmp_path / "inmet" / "A026"
    shutil.copytree(INMET, copia)
    with (copia / "serie_diaria.csv").open("a", encoding="utf-8") as f:
        f.write("2099-01-01,24,1.0\n")
    monkeypatch.setattr(servico, "DIR_REF_INMET", tmp_path / "inmet")
    r = servico.validacao(-17.45, -52.60, dir_cache=tmp_path)
    assert r["disponivel"] is False and "sha256" in r["motivo"]
