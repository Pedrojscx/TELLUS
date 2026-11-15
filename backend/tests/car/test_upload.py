"""Upload do shapefile SICAR e confirmação da lavoura (FR-003, FR-004)."""

import io
import json
import zipfile
from pathlib import Path

import pytest
import shapefile
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.car import servico

FIX = Path(__file__).parent / "fixtures"
PRJ_GEO = 'GEOGCS["SIRGAS 2000",DATUM["Sistema_de_Referencia_Geocentrico_para_las_AmericaS_2000",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]]'
PRJ_UTM = 'PROJCS["SIRGAS 2000 / UTM zone 22S",GEOGCS["SIRGAS 2000"],PROJECTION["Transverse_Mercator"]]'


def zip_shp(aneis, prj=PRJ_GEO, sem=()):
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
    w.field("cod_imovel", "C")
    for anel in aneis:
        w.poly([anel])
        w.record("GO-teste")
    w.close()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for nome, buf in (("area.shp", shp), ("area.shx", shx), ("area.dbf", dbf)):
            if nome.rsplit(".", 1)[1] not in sem:
                z.writestr(nome, buf.getvalue())
        if prj:
            z.writestr("area.prj", prj)
    return out.getvalue()


# sentido horário (convenção do shapefile para contorno externo)
ANEL = [[-51.10, -17.89], [-51.10, -17.88], [-51.09, -17.88], [-51.09, -17.89], [-51.10, -17.89]]


def test_upload_valido():
    r = servico.upload_sicar(zip_shp([ANEL]), "imovel.zip")
    c = r["candidato"]
    assert c["origem"] == "upload_sicar" and c["estado"] == "aguardando_confirmacao"
    assert c["area_ha"] == pytest.approx(117.6, rel=0.02)  # 0,01° × 0,01° a 17,9°S
    assert c["municipios"][0]["nome"] == "Rio Verde"


def test_upload_sem_dbf():
    with pytest.raises(servico.ErroCar) as e:
        servico.upload_sicar(zip_shp([ANEL], sem=("dbf",)))
    assert e.value.codigo == "arquivo_invalido" and ".dbf" in e.value.mensagem


def test_upload_utm_recusado():
    with pytest.raises(servico.ErroCar) as e:
        servico.upload_sicar(zip_shp([ANEL], prj=PRJ_UTM))
    assert e.value.codigo == "projecao_nao_suportada"


def test_upload_nao_zip():
    with pytest.raises(servico.ErroCar) as e:
        servico.upload_sicar(b"isto nao e zip")
    assert e.value.codigo == "arquivo_invalido"


def test_confirmar_e_id_divergente():
    c = servico.upload_sicar(zip_shp([ANEL]))["candidato"]
    lav = servico.confirmar(c["geometria"], c["id_geometria"], "upload_sicar")
    assert lav["estado"] == "confirmada"
    assert lav["localizacao"]["local"]["municipio"]["codigo_ibge"] == "5218805"
    with pytest.raises(servico.ErroCar) as e:
        servico.confirmar(c["geometria"], "0" * 64, "upload_sicar")
    assert e.value.codigo == "geometria_alterada"


def test_api_upload_e_confirmar():
    cli = TestClient(app)
    r = cli.post("/api/car/upload", files={"arquivo": ("imovel.zip", zip_shp([ANEL]), "application/zip")})
    assert r.status_code == 200
    c = r.json()["candidato"]
    r2 = cli.post("/api/lavoura/confirmar", json={"geometria": c["geometria"], "id_geometria": c["id_geometria"], "origem": "upload_sicar"})
    assert r2.status_code == 200 and r2.json()["estado"] == "confirmada"
    r3 = cli.post("/api/car/upload", files={"arquivo": ("x.zip", b"nada", "application/zip")})
    assert r3.status_code == 422 and r3.json()["erro"]["codigo"] == "arquivo_invalido"


def test_api_codigo_invalido():
    r = TestClient(app).get("/api/car/GO-123")
    assert r.status_code == 200 and r.json()["estado"] == "codigo_invalido"
