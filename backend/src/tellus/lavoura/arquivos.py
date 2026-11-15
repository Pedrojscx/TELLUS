"""Leitura de arquivo georreferenciado da lavoura (spec 002, #22, #24): KML, KMZ, GeoJSON e Shapefile .zip.

Só stdlib (xml.etree, zipfile, json) mais o leitor de shapefile que já existia (`tellus.car.shapefile`, pyshp).
Uma lavoura por envio (D-009): o arquivo precisa trazer exatamente um Polygon ou um MultiPolygon. Vários
polígonos soltos (várias feições/Placemarks) viram o erro `varias_lavouras`, nunca uma união silenciosa.
"""

from __future__ import annotations

import io
import json
import zipfile
from xml.etree import ElementTree as ET

from tellus.car import shapefile as shp

FORMATOS = {"kml": "KML", "kmz": "KMZ", "geojson": "GeoJSON", "shapefile_zip": "Shapefile .zip"}
EXTENSOES = {".kml": "kml", ".kmz": "kmz", ".geojson": "geojson", ".json": "geojson", ".zip": "shapefile_zip"}


class ErroArquivo(Exception):
    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo, self.mensagem = codigo, mensagem


def formato_do_nome(nome: str, aceitos: list[str]) -> str:
    n = (nome or "").lower().strip()
    fmt = next((f for ext, f in EXTENSOES.items() if n.endswith(ext)), None)
    if fmt is None or fmt not in aceitos:
        lista = ", ".join(FORMATOS[f] for f in aceitos)
        raise ErroArquivo("formato_nao_aceito", f"Formato não aceito ({nome or 'sem nome'}). Envie um destes: {lista}.")
    return fmt


def _zip(conteudo: bytes, limite_bytes: int) -> zipfile.ZipFile:
    try:
        zf = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile as e:
        raise ErroArquivo("arquivo_invalido", "O arquivo não é um .zip/.kmz válido.") from e
    if sum(i.file_size for i in zf.infolist()) > limite_bytes:  # proteção contra zip-bomba
        raise ErroArquivo("arquivo_grande", "O conteúdo descompactado passa do limite de tamanho de arquivo.")
    return zf


# ---------------------------------------------------------------- KML / KMZ


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _coords(texto: str | None) -> list[list[float]]:
    pts = []
    for tupla in (texto or "").split():
        partes = tupla.split(",")
        if len(partes) < 2:
            raise ErroArquivo("arquivo_invalido", f"Coordenada KML malformada: '{tupla[:40]}'.")
        try:
            pts.append([float(partes[0]), float(partes[1])])
        except ValueError as e:
            raise ErroArquivo("arquivo_invalido", f"Coordenada KML não numérica: '{tupla[:40]}'.") from e
    return pts


def _poligono_kml(el: ET.Element) -> list[list[list[float]]]:
    aneis = []
    for lado in ("outerBoundaryIs", "innerBoundaryIs"):
        for b in (x for x in el if _local(x.tag) == lado):
            for anel in (x for x in b.iter() if _local(x.tag) == "LinearRing"):
                c = next((x for x in anel if _local(x.tag) == "coordinates"), None)
                aneis.append(_coords(c.text if c is not None else ""))
    if not aneis:
        raise ErroArquivo("arquivo_invalido", "Polígono KML sem contorno (outerBoundaryIs).")
    return aneis


def ler_kml(conteudo: bytes) -> list[dict]:
    """Uma geometria por Placemark com polígono(s). MultiGeometry com vários polígonos = um MultiPolygon."""
    cab = conteudo[:4096].upper()
    if b"<!DOCTYPE" in cab or b"<!ENTITY" in conteudo.upper():
        raise ErroArquivo("arquivo_invalido", "O KML traz declarações DOCTYPE/ENTITY, que não são aceitas.")
    try:
        raiz = ET.fromstring(conteudo)
    except ET.ParseError as e:
        raise ErroArquivo("arquivo_invalido", f"O KML não é um XML válido ({e}).") from e
    if _local(raiz.tag) != "kml":
        raise ErroArquivo("arquivo_invalido", "O arquivo não é um KML (falta o elemento <kml>).")
    geoms = []
    for pm in (x for x in raiz.iter() if _local(x.tag) == "Placemark"):
        pols = [_poligono_kml(p) for p in pm.iter() if _local(p.tag) == "Polygon"]
        if len(pols) == 1:
            geoms.append({"type": "Polygon", "coordinates": pols[0]})
        elif pols:
            geoms.append({"type": "MultiPolygon", "coordinates": pols})
    return geoms


def ler_kmz(conteudo: bytes, limite_bytes: int) -> list[dict]:
    zf = _zip(conteudo, limite_bytes)
    kmls = sorted(n for n in zf.namelist() if n.lower().endswith(".kml"))
    if not kmls:
        raise ErroArquivo("arquivo_invalido", "O KMZ não contém nenhum arquivo .kml.")
    principal = "doc.kml" if "doc.kml" in kmls else kmls[0]
    return ler_kml(zf.read(principal))


# ---------------------------------------------------------------- GeoJSON


def _geom_geojson(g) -> list[dict]:
    if not isinstance(g, dict):
        return []
    t = g.get("type")
    if t in ("Polygon", "MultiPolygon"):
        if not isinstance(g.get("coordinates"), list):
            raise ErroArquivo("arquivo_invalido", f"{t} sem coordenadas.")
        return [{"type": t, "coordinates": g["coordinates"]}]
    if t == "GeometryCollection":
        return [x for sub in g.get("geometries") or [] for x in _geom_geojson(sub)]
    return []  # pontos e linhas não são lavoura


def ler_geojson(conteudo: bytes) -> list[dict]:
    try:
        d = json.loads(conteudo.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ErroArquivo("arquivo_invalido", f"O GeoJSON não é um JSON válido ({e.__class__.__name__}).") from e
    if not isinstance(d, dict) or "type" not in d:
        raise ErroArquivo("arquivo_invalido", "O arquivo não é GeoJSON (falta 'type').")
    crs = ((d.get("crs") or {}).get("properties") or {}).get("name", "")
    if crs and not any(s in crs.upper() for s in ("4326", "CRS84", "4674")):
        raise ErroArquivo("projecao_nao_suportada", f"O GeoJSON declara o sistema {crs}. Use coordenadas geográficas (WGS 84).")
    if d["type"] == "FeatureCollection":
        return [g for f in d.get("features") or [] if isinstance(f, dict) for g in _geom_geojson(f.get("geometry"))]
    if d["type"] == "Feature":
        return _geom_geojson(d.get("geometry"))
    return _geom_geojson(d)


# ---------------------------------------------------------------- entrada única


def ler(conteudo: bytes, nome: str, aceitos: list[str], limite_bytes: int) -> tuple[dict, dict]:
    """(geometria única, info). Erros nomeados: formato_nao_aceito, arquivo_invalido, projecao_nao_suportada,
    sem_geometria, varias_lavouras, arquivo_grande."""
    fmt = formato_do_nome(nome, aceitos)
    if fmt == "kml":
        geoms = ler_kml(conteudo)
    elif fmt == "kmz":
        geoms = ler_kmz(conteudo, limite_bytes)
    elif fmt == "geojson":
        geoms = ler_geojson(conteudo)
    else:
        _zip(conteudo, limite_bytes)
        try:
            geoms, _ = shp.ler_zip(conteudo)
        except shp.ErroArquivo as e:
            raise ErroArquivo(e.codigo, e.mensagem) from e
    if not geoms:
        raise ErroArquivo("sem_geometria", f"O arquivo {FORMATOS[fmt]} não tem nenhum polígono (Polygon ou MultiPolygon).")
    if len(geoms) > 1:
        raise ErroArquivo("varias_lavouras", f"O arquivo tem {len(geoms)} polígonos separados. Envie uma lavoura por arquivo "
                          "(um polígono, ou um MultiPolygon para uma lavoura em partes).")
    return geoms[0], {"formato": fmt, "nome_formato": FORMATOS[fmt], "arquivo": nome, "bytes": len(conteudo)}
