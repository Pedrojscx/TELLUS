"""Cliente do NASA POWER diário (variáveis da ETo), com cache por célula."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import httpx

from tellus.localizacao.regras import celula_power

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETROS = ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "RH2M", "WS2M", "PRECTOTCORR"]
INICIO_PADRAO = dt.date(2001, 1, 1)
FILL = -999.0


def chave_celula(lat: float, lon: float) -> tuple[str, float, float]:
    clat, clon = celula_power(lat, lon)
    return f"{clat:+.3f}_{clon:+.3f}", clat, clon


def arquivo_cache(dir_cache: Path, lat: float, lon: float) -> Path:
    chave, _, _ = chave_celula(lat, lon)
    return dir_cache / "power" / f"{chave}.json"


def baixar(dir_cache: Path, lat: float, lon: float, inicio: dt.date = INICIO_PADRAO, fim: dt.date | None = None) -> Path:
    """Baixa o período inteiro num pedido, consultando o centro da célula (resposta canônica)."""
    _, clat, clon = chave_celula(lat, lon)
    fim = fim or dt.date.today()
    params = {
        "parameters": ",".join(PARAMETROS),
        "community": "AG",
        "longitude": clon,
        "latitude": clat,
        "start": f"{inicio:%Y%m%d}",
        "end": f"{fim:%Y%m%d}",
        "format": "JSON",
        "time-standard": "UTC",
    }
    r = httpx.get(URL, params=params, timeout=180)
    r.raise_for_status()
    p = arquivo_cache(dir_cache, lat, lon)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(r.content)
    meta = {
        "url": str(r.url),
        "obtido_em": dt.date.today().isoformat(),
        "status_http": r.status_code,
        "sha256": hashlib.sha256(r.content).hexdigest(),
    }
    p.with_suffix(".json.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return p


def ler(p: Path) -> dict:
    """Devolve {'dias': {AAAA-MM-DD: {param: valor|None}}, 'altitude_m', 'unidades', 'fontes', 'obtido_em', 'url'}."""
    bruto = json.loads(p.read_text(encoding="utf-8"))
    meta_p = p.with_suffix(".json.meta.json")
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    param = bruto["properties"]["parameter"]
    fill = bruto.get("header", {}).get("fill_value", FILL)
    dias: dict[str, dict] = {}
    for nome, serie in param.items():
        for k, v in serie.items():
            data = f"{k[:4]}-{k[4:6]}-{k[6:]}"
            dias.setdefault(data, {})[nome] = None if v is None or v == fill else float(v)
    return {
        "dias": dias,
        "altitude_m": bruto["geometry"]["coordinates"][2] if len(bruto["geometry"]["coordinates"]) > 2 else None,
        "unidades": {k: v.get("units") for k, v in bruto.get("parameters", {}).items()},
        "fontes": bruto.get("header", {}).get("sources", []),
        "obtido_em": meta.get("obtido_em"),
        "url": meta.get("url", URL),
    }
