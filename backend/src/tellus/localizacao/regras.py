"""Regras puras de localização: sem rede, sem relógio, sem estado global (Princípio IV)."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

RAIO_TERRA_KM = 6371.0088  # raio médio da Terra (IUGG)
PASSO_POWER_LAT = 0.5
PASSO_POWER_LON = 0.625
PASSO_IMERG = 0.1

T = TypeVar("T")
Anel = Sequence[Sequence[float]]  # [[lon, lat], ...]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância de grande círculo em km."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df = f2 - f1
    dl = math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


def celula_power(lat: float, lon: float) -> tuple[float, float]:
    """Centro da célula NASA POWER (0,5° × 0,625°) que contém o ponto (research R5)."""
    return (
        round(round(lat / PASSO_POWER_LAT) * PASSO_POWER_LAT, 4),
        round(round(lon / PASSO_POWER_LON) * PASSO_POWER_LON, 4),
    )


def celula_imerg(lat: float, lon: float) -> tuple[float, float]:
    """Centro da célula IMERG (0,1°) que contém o ponto (research R6)."""
    # Arredonda antes do floor para evitar erro de ponto flutuante (ex.: -17.8/0.1).
    def centro(v: float) -> float:
        return round(math.floor(round(v / PASSO_IMERG, 9)) * PASSO_IMERG + PASSO_IMERG / 2, 4)

    return centro(lat), centro(lon)


def _ponto_em_anel(lon: float, lat: float, anel: Anel) -> bool:
    dentro = False
    n = len(anel)
    j = n - 1
    for i in range(n):
        xi, yi = anel[i][0], anel[i][1]
        xj, yj = anel[j][0], anel[j][1]
        if (yi > lat) != (yj > lat):
            x_corte = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_corte:
                dentro = not dentro
        j = i
    return dentro


def ponto_em_poligono(lat: float, lon: float, geometria: dict) -> bool:
    """Ray casting para GeoJSON Polygon ou MultiPolygon, respeitando buracos."""
    tipo = geometria["type"]
    if tipo == "Polygon":
        poligonos = [geometria["coordinates"]]
    elif tipo == "MultiPolygon":
        poligonos = geometria["coordinates"]
    else:
        raise ValueError(f"geometria não suportada: {tipo}")
    for aneis in poligonos:
        if _ponto_em_anel(lon, lat, aneis[0]) and not any(
            _ponto_em_anel(lon, lat, buraco) for buraco in aneis[1:]
        ):
            return True
    return False


def dentro_do_bbox(lat: float, lon: float, bbox: Sequence[float], folga: float = 0.0) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lon - folga) <= lon <= (max_lon + folga) and (min_lat - folga) <= lat <= (
        max_lat + folga
    )


def distancia_ao_anel_km(lat: float, lon: float, anel: Anel) -> float:
    """Distância aproximada (km) do ponto ao contorno, pelo vértice/segmento mais próximo.

    Projeção equiretangular local: suficiente para limiares de poucos km (divisa).
    """
    kx = math.cos(math.radians(lat)) * 111.32
    ky = 110.574
    px, py = lon * kx, lat * ky
    melhor = math.inf
    for (x0, y0), (x1, y1) in zip(anel, anel[1:]):
        ax, ay, bx, by = x0 * kx, y0 * ky, x1 * kx, y1 * ky
        dx, dy = bx - ax, by - ay
        comp2 = dx * dx + dy * dy
        t = 0.0 if comp2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / comp2))
        cx, cy = ax + t * dx, ay + t * dy
        melhor = min(melhor, math.hypot(px - cx, py - cy))
    return melhor


def distancia_a_geometria_km(lat: float, lon: float, geometria: dict) -> float:
    if geometria["type"] == "Polygon":
        aneis = [geometria["coordinates"][0]]
    else:
        aneis = [p[0] for p in geometria["coordinates"]]
    return min(distancia_ao_anel_km(lat, lon, a) for a in aneis)


def mais_proximo(
    lat: float,
    lon: float,
    itens: Iterable[T],
    coordenadas: Callable[[T], tuple[float, float]],
    identificador: Callable[[T], str],
) -> tuple[T, float] | None:
    """Item mais próximo e distância em km; empate decidido pelo identificador."""
    melhor: tuple[float, str, T] | None = None
    for item in itens:
        ilat, ilon = coordenadas(item)
        d = haversine_km(lat, lon, ilat, ilon)
        chave = (round(d, 6), identificador(item))
        if melhor is None or chave < (melhor[0], melhor[1]):
            melhor = (chave[0], chave[1], item)
    if melhor is None:
        return None
    return melhor[2], melhor[0]
