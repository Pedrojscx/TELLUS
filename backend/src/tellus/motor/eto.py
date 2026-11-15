"""ETo diária por FAO-56 Penman-Monteith (Allen et al., 1998, eq. 6 e cap. 3). Puro."""

from __future__ import annotations

import math

SIGMA = 4.903e-9  # MJ K-4 m-2 dia-1
GSC = 0.0820  # MJ m-2 min-1


def es(t: float) -> float:
    """Pressão de saturação (kPa), eq. 11."""
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def ra(lat_graus: float, doy: int) -> float:
    """Radiação extraterrestre (MJ m-2 dia-1), eq. 21."""
    phi = math.radians(lat_graus)
    dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
    delta = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return 24 * 60 / math.pi * GSC * dr * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))


def eto(tmax: float, tmin: float, rs: float, u2: float, altitude_m: float, lat: float, doy: int,
        ea: float | None = None, ur_media: float | None = None) -> dict:
    """ETo (mm/dia) e intermediários. Usa `ea` (kPa) se dado; senão estima pela UR média (eq. 19)."""
    tmed = (tmax + tmin) / 2
    p = 101.3 * ((293 - 0.0065 * altitude_m) / 293) ** 5.26
    gama = 0.665e-3 * p
    es_ = (es(tmax) + es(tmin)) / 2
    if ea is None:
        if ur_media is None:
            raise ValueError("informe ea ou a umidade relativa média")
        ea = ur_media / 100 * es_
    delta = 4098 * es(tmed) / (tmed + 237.3) ** 2
    ra_ = ra(lat, doy)
    rso = (0.75 + 2e-5 * altitude_m) * ra_
    rns = (1 - 0.23) * rs
    rel = min(rs / rso, 1.0) if rso > 0 else 0.0
    rnl = SIGMA * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * rel - 0.35)
    rn = rns - rnl
    num = 0.408 * delta * rn + gama * 900 / (tmed + 273) * u2 * (es_ - ea)
    den = delta + gama * (1 + 0.34 * u2)
    return {"eto": max(0.0, num / den), "rn": rn, "ra": ra_, "rso": rso, "rnl": rnl, "es": es_, "ea": ea, "delta": delta, "gama": gama}
