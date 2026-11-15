"""Regras puras de geometria da lavoura (Princípio VI): código CAR, validação, área, municípios.

Usadas pela spec 001 (CAR) e reaproveitáveis pela spec 002 (desenho e upload).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable

from tellus.localizacao.regras import dentro_do_bbox, ponto_em_poligono

RAIO_M = 6371008.8
PADRAO_CODIGO = re.compile(r"^[A-Z]{2}-\d{7}-[0-9A-F]{32}$")
UFS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI",
    "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}


# ------------------------------------------------------------------ código CAR


def normalizar_codigo(texto: str) -> str | None:
    """Código no formato UF-IBGE7-HASH32 ou None se inválido (sem tocar na rede)."""
    c = re.sub(r"[\s.]", "", str(texto or "")).upper()
    if not PADRAO_CODIGO.match(c) or c[:2] not in UFS:
        return None
    return c


# ------------------------------------------------------------------ geometria


def poligonos(geom: dict) -> list[list[list[list[float]]]]:
    """Lista de polígonos (cada um = lista de anéis) de um Polygon ou MultiPolygon."""
    if geom.get("type") == "Polygon":
        return [geom["coordinates"]]
    if geom.get("type") == "MultiPolygon":
        return list(geom["coordinates"])
    raise ValueError(f"tipo de geometria não suportado: {geom.get('type')}")


def _orient(ax, ay, bx, by, cx, cy) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _segmentos_cruzam(p1, p2, p3, p4) -> bool:
    d1 = _orient(*p3, *p4, *p1)
    d2 = _orient(*p3, *p4, *p2)
    d3 = _orient(*p1, *p2, *p3)
    d4 = _orient(*p1, *p2, *p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4):
        return True
    return False


def anel_autointersecta(anel: list[list[float]]) -> bool:
    """Varredura por x: só compara segmentos cujos intervalos em x se sobrepõem."""
    pts = [(p[0], p[1]) for p in anel]
    n = len(pts) - 1  # último = primeiro
    segs = sorted(
        ((min(pts[i][0], pts[i + 1][0]), max(pts[i][0], pts[i + 1][0]), i) for i in range(n)),
        key=lambda s: s[0],
    )
    ativos: list[tuple[float, int]] = []
    for xmin, xmax, i in segs:
        ativos = [(xm, j) for xm, j in ativos if xm >= xmin]
        for _, j in ativos:
            if abs(i - j) in (1, n - 1):  # vizinhos compartilham vértice
                continue
            if _segmentos_cruzam(pts[i], pts[i + 1], pts[j], pts[j + 1]):
                return True
        ativos.append((xmax, i))
    return False


def _area_m2_anel(anel: list[list[float]], lat0: float, lon0: float) -> float:
    """Área (com sinal) do anel projetado em Lambert azimutal equivalente centrado em (lat0, lon0)."""
    f0, l0 = math.radians(lat0), math.radians(lon0)
    xy = []
    for lon, lat in ((p[0], p[1]) for p in anel):
        f, dl = math.radians(lat), math.radians(lon) - l0
        k = math.sqrt(2 / (1 + math.sin(f0) * math.sin(f) + math.cos(f0) * math.cos(f) * math.cos(dl)))
        xy.append((RAIO_M * k * math.cos(f) * math.sin(dl),
                   RAIO_M * k * (math.cos(f0) * math.sin(f) - math.sin(f0) * math.cos(f) * math.cos(dl))))
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(xy, xy[1:])) / 2


def centroide_bbox(geom: dict) -> tuple[float, float]:
    xs = [p[0] for pol in poligonos(geom) for p in pol[0]]
    ys = [p[1] for pol in poligonos(geom) for p in pol[0]]
    return (min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2


def area_ha(geom: dict) -> float:
    lat0, lon0 = centroide_bbox(geom)
    total = 0.0
    for pol in poligonos(geom):
        externo = abs(_area_m2_anel(pol[0], lat0, lon0))
        buracos = sum(abs(_area_m2_anel(b, lat0, lon0)) for b in pol[1:])
        total += externo - buracos
    return total / 10_000


def validar_poligono(geom: dict, max_vertices: int = 5000) -> list[str]:
    """Lista de motivos de invalidez (vazia = válido)."""
    try:
        pols = poligonos(geom)
    except (ValueError, KeyError, TypeError) as e:
        return [str(e)]
    motivos: list[str] = []
    if not pols:
        return ["geometria vazia"]
    for ip, pol in enumerate(pols, 1):
        if not pol:
            motivos.append(f"parte {ip}: sem anéis")
            continue
        for ia, anel in enumerate(pol):
            nome = f"parte {ip}, {'contorno' if ia == 0 else f'buraco {ia}'}"
            if len(anel) < 4:
                motivos.append(f"{nome}: menos de 4 posições")
                continue
            if any(len(p) < 2 or not all(math.isfinite(float(v)) for v in p[:2]) for p in anel):
                motivos.append(f"{nome}: coordenada inválida")
                continue
            if any(not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90) for p in anel):
                motivos.append(f"{nome}: coordenada fora da faixa geográfica (use graus decimais)")
                continue
            if list(anel[0][:2]) != list(anel[-1][:2]):
                motivos.append(f"{nome}: anel não fechado")
                continue
            if len(anel) > max_vertices:
                motivos.append(f"{nome}: mais de {max_vertices} vértices")
                continue
            if anel_autointersecta(anel):
                motivos.append(f"{nome}: o contorno cruza a si mesmo")
    if not motivos and area_ha(geom) <= 0:
        motivos.append("área nula")
    return motivos


def canonica(geom: dict, casas: int = 6) -> dict:
    """Geometria como MultiPolygon com coordenadas arredondadas (id estável)."""
    return {
        "type": "MultiPolygon",
        "coordinates": [[[[round(float(p[0]), casas), round(float(p[1]), casas)] for p in anel] for anel in pol]
                        for pol in poligonos(geom)],
    }


def id_geometria(geom: dict, casas: int = 6) -> str:
    texto = json.dumps(canonica(geom, casas), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()


def pontos_amostra(geom: dict, max_pontos: int = 400) -> list[tuple[float, float]]:
    """Grade regular dentro do polígono (lat, lon), mais os vértices do contorno."""
    xs = [p[0] for pol in poligonos(geom) for p in pol[0]]
    ys = [p[1] for pol in poligonos(geom) for p in pol[0]]
    lado = max(1, int(math.sqrt(max_pontos)))
    pts = []
    for i in range(lado):
        lat = min(ys) + (i + 0.5) * (max(ys) - min(ys)) / lado
        for j in range(lado):
            lon = min(xs) + (j + 0.5) * (max(xs) - min(xs)) / lado
            if ponto_em_poligono(lat, lon, geom):
                pts.append((lat, lon))
    return pts or [centroide_bbox(geom)]


def municipios_atingidos(geom: dict, municipios: dict[str, dict], malha: dict[str, dict]) -> list[dict]:
    """Municípios que a área atinge, com a fração aproximada da área (soma 1)."""
    contagem: dict[str, int] = {}
    vertices = [(p[1], p[0]) for pol in poligonos(geom) for p in pol[0][:-1]]
    for lat, lon in pontos_amostra(geom) + vertices:
        cod = _municipio(lat, lon, municipios, malha)
        if cod:
            contagem[cod] = contagem.get(cod, 0) + 1
    total = sum(contagem.values()) or 1
    return [
        {"codigo_ibge": c, "nome": municipios[c]["nome"], "uf": municipios[c]["uf"], "fracao": round(n / total, 3)}
        for c, n in sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def _municipio(lat: float, lon: float, municipios: dict[str, dict], malha: dict[str, dict]) -> str | None:
    for cod, g in malha.items():
        m = municipios.get(cod)
        if m and m.get("bbox") and dentro_do_bbox(lat, lon, m["bbox"]) and ponto_em_poligono(lat, lon, g):
            return cod
    return None


def uniao(geoms: Iterable[dict]) -> dict:
    """Junta várias geometrias num MultiPolygon (sem dissolver fronteiras)."""
    return {"type": "MultiPolygon", "coordinates": [pol for g in geoms for pol in poligonos(g)]}
