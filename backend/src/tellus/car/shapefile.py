"""Leitura do shapefile exportado do SICAR (.zip) em Python puro (research R6)."""

from __future__ import annotations

import io
import zipfile

import shapefile  # pyshp


class ErroArquivo(Exception):
    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo, self.mensagem = codigo, mensagem


def ler_zip(conteudo: bytes) -> tuple[list[dict], dict]:
    """Geometrias GeoJSON e informações do arquivo. Exige .shp, .shx e .dbf; .prj geográfico."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile as e:
        raise ErroArquivo("arquivo_invalido", "O arquivo enviado não é um .zip válido.") from e
    nomes = [n for n in zf.namelist() if not n.endswith("/")]
    por_ext: dict[str, str] = {}
    for n in nomes:
        ext = n.rsplit(".", 1)[-1].lower() if "." in n else ""
        por_ext.setdefault(ext, n)
    faltam = [e for e in ("shp", "shx", "dbf") if e not in por_ext]
    if faltam:
        raise ErroArquivo("arquivo_invalido", "Faltam no .zip os arquivos: " + ", ".join(f".{e}" for e in faltam) + ".")
    if "prj" in por_ext:
        prj = zf.read(por_ext["prj"]).decode("latin-1", "ignore").upper()
        if prj.startswith("PROJCS") or "PROJECTION[" in prj:
            raise ErroArquivo(
                "projecao_nao_suportada",
                "O shapefile está em coordenadas projetadas (ex.: UTM). Exporte do SICAR em coordenadas geográficas.",
            )
    leitor = shapefile.Reader(
        shp=io.BytesIO(zf.read(por_ext["shp"])),
        shx=io.BytesIO(zf.read(por_ext["shx"])),
        dbf=io.BytesIO(zf.read(por_ext["dbf"])),
    )
    geoms = []
    for forma in leitor.shapes():
        g = forma.__geo_interface__
        if g.get("type") in ("Polygon", "MultiPolygon"):
            geoms.append({"type": g["type"], "coordinates": _listas(g["coordinates"])})
    if not geoms:
        raise ErroArquivo("sem_geometria", "O shapefile não tem nenhum polígono.")
    campos = [f[0] for f in leitor.fields[1:]]
    registros = [dict(zip(campos, r)) for r in leitor.records()]
    return geoms, {"arquivos": nomes, "feicoes": len(geoms), "campos": campos, "registros": registros[:5]}


def _listas(x):
    if isinstance(x, (list, tuple)):
        if x and isinstance(x[0], (int, float)):
            return [float(v) for v in x]
        return [_listas(v) for v in x]
    return x
