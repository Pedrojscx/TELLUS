"""Série REAL versionada de Rio Verde-GO: SPL3SMP_E V006, célula EASE2_M09 L1059/C1382.

Obtida da NSIDC por OPeNDAP em 2026-11-15 (scripts/preparar_umidade.py, 2026-10-17..2026-11-15).
Os números abaixo foram contados também direto dos 27 recortes brutos em data/raw/umidade/.
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import umidade
from tellus.umidade import servico

from .conftest import CEL_M09

REF = servico.RAIZ / "referencias" / "umidade"
pytestmark = pytest.mark.skipif(not (REF / "rio_verde_go" / "serie.csv").exists(), reason="série real não versionada")


@pytest.fixture
def so_referencia(monkeypatch, tmp_path):
    monkeypatch.setattr(servico, "DIR_REFERENCIA", REF)
    return tmp_path  # cache local vazio: força a série versionada


def test_amostra_real_contagem(so_referencia):
    r = servico.contexto(-17.785, -50.965, dir_cache=so_referencia)
    assert r["dado_sintetico"] is False and r["origem_dados"] == "referencia_versionada"
    assert (r["celulas"][0]["linha"], r["celulas"][0]["coluna"]) == CEL_M09
    assert r["regra_periodo"]["contagem"] == {
        "observacoes_validas": 17, "registros_sem_dado": 36, "registros_qualidade_nao_recomendada": 1,
        "dias_sem_registro": 3, "passagens_possiveis": 60,
    }
    itens = r["itens"]
    assert len(itens) == 17 and all(i["estado"] == "disponivel" for i in itens)
    assert sum(i["periodo"]["variante"] == "AM" for i in itens) == 10
    valores = [i["valor"] for i in itens]
    assert (min(valores), max(valores)) == (0.1897, 0.3594)
    assert all(i["qualidade"]["recomendada"] is True for i in itens)
    assert "2026-11-08" not in {i["periodo"]["data"] for i in itens if i["periodo"]["variante"] == "PM"}  # flag 9: bit 0 = 1


def test_rota_real_200_com_aviso_de_escala(so_referencia, monkeypatch):
    monkeypatch.setattr(servico, "DIR_CACHE", so_referencia)
    app = FastAPI()
    app.include_router(umidade.router)
    r = TestClient(app).get("/api/umidade/contexto", params={"lat": -17.785, "lon": -50.965})
    assert r.status_code == 200
    j = r.json()
    assert j["dado_sintetico"] is False and len(j["itens"]) == 17
    assert all(i["aviso_escala"]["espacial"] and i["aviso_escala"]["temporal"] for i in j["itens"])
    assert any(a["codigo"] == "referencia_versionada" for a in j["avisos"])


def test_sem_cache_e_sem_referencia_continua_404(monkeypatch, tmp_path):
    monkeypatch.setattr(servico, "DIR_REFERENCIA", None)
    with pytest.raises(servico.ErroUmidade) as e:
        servico.contexto(-17.785, -50.965, dir_cache=tmp_path)
    assert e.value.codigo == "sem_cache"


def test_referencia_com_hash_divergente_e_ignorada(monkeypatch, tmp_path):
    copia = tmp_path / "ref" / "rio_verde_go"
    copia.mkdir(parents=True)
    (copia / "meta.json").write_text((REF / "rio_verde_go" / "meta.json").read_text(encoding="utf-8"), encoding="utf-8")
    (copia / "serie.csv").write_text((REF / "rio_verde_go" / "serie.csv").read_text(encoding="utf-8") + "x\n", encoding="utf-8")
    monkeypatch.setattr(servico, "DIR_REFERENCIA", tmp_path / "ref")
    with pytest.raises(servico.ErroUmidade):
        servico.contexto(-17.785, -50.965, dir_cache=tmp_path / "vazio")


def test_meta_versionado_sem_credencial():
    texto = (REF / "rio_verde_go" / "meta.json").read_text(encoding="utf-8")
    meta = json.loads(texto)
    assert meta["sintetico"] is False and meta["versao"] == "006"
    assert "authorization" not in texto.lower() and "bearer" not in texto.lower()
