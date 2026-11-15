"""Geradores de arquivos SINTÉTICOS de teste (KML, KMZ, GeoJSON, Shapefile .zip) e a geometria real do CAR gravada.

Os arquivos são montados no próprio teste a partir de coordenadas; não são dados reais de produtor,
exceto `GEOM_CAR`, o limite real do imóvel GO-5218805-8F8B…EE33 já gravado nos testes do CAR.
"""

import io
import json
import zipfile
from pathlib import Path

import pytest
import shapefile

FIX_CAR = Path(__file__).resolve().parents[1] / "car" / "fixtures" / "encontrado.json"
PRJ_GEO = 'GEOGCS["SIRGAS 2000",DATUM["SIRGAS_2000",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]]'
# Rio Verde-GO; sentido horário (convenção do shapefile para contorno externo)
ANEL = [[-51.10, -17.89], [-51.10, -17.88], [-51.09, -17.88], [-51.09, -17.89], [-51.10, -17.89]]


def geom_car() -> dict:
    return json.loads(FIX_CAR.read_text(encoding="utf-8"))["features"][0]["geometry"]


def kml(geoms: list[dict], extra: str = "") -> bytes:
    def anel(a):
        return " ".join(f"{x},{y},0" for x, y in a)

    def pol(coords):
        out = f"<outerBoundaryIs><LinearRing><coordinates>{anel(coords[0])}</coordinates></LinearRing></outerBoundaryIs>"
        out += "".join(f"<innerBoundaryIs><LinearRing><coordinates>{anel(h)}</coordinates></LinearRing></innerBoundaryIs>" for h in coords[1:])
        return f"<Polygon>{out}</Polygon>"

    pms = []
    for g in geoms:
        if g["type"] == "Polygon":
            pms.append(f"<Placemark><name>lavoura</name>{pol(g['coordinates'])}</Placemark>")
        else:
            pms.append("<Placemark><MultiGeometry>" + "".join(pol(p) for p in g["coordinates"]) + "</MultiGeometry></Placemark>")
    return (f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>{extra}'
            + "".join(pms) + "</Document></kml>").encode()


def kmz(conteudo_kml: bytes, nome: str = "doc.kml") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(nome, conteudo_kml)
    return out.getvalue()


def geojson(geoms: list[dict], como: str = "FeatureCollection") -> bytes:
    if como == "Geometry":
        return json.dumps(geoms[0]).encode()
    feats = [{"type": "Feature", "properties": {"sintetico": True}, "geometry": g} for g in geoms]
    return json.dumps(feats[0] if como == "Feature" else {"type": "FeatureCollection", "features": feats}).encode()


def zip_shp(geoms: list[dict]) -> bytes:
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
    w.field("origem", "C")
    for g in geoms:
        partes = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        w.poly([anel for p in partes for anel in p])
        w.record("sintetico")
    w.close()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for nome, buf in (("area.shp", shp), ("area.shx", shx), ("area.dbf", dbf)):
            z.writestr(nome, buf.getvalue())
        z.writestr("area.prj", PRJ_GEO)
    return out.getvalue()


GERADORES = {
    "area.kml": lambda gs: kml(gs),
    "area.kmz": lambda gs: kmz(kml(gs)),
    "area.geojson": lambda gs: geojson(gs),
    "area.zip": lambda gs: zip_shp(gs),
}


@pytest.fixture
def poligono():
    return {"type": "Polygon", "coordinates": [ANEL]}
