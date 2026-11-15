"""Cliente do WFS público do SICAR, com cache por código (research R1)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import httpx

URL = "https://geoserver.car.gov.br/geoserver/sicar/wfs"
VERSAO = "SICAR WFS 2.0.0"
RAIZ = Path(__file__).resolve().parents[4]
DIR_CACHE = Path(os.environ.get("TELLUS_CACHE_CAR", RAIZ / "data" / "raw" / "car"))


class FonteIndisponivel(Exception):
    pass


def camada(codigo: str) -> str:
    return f"sicar:sicar_imoveis_{codigo[:2].lower()}"


def parametros(codigo: str) -> dict:
    return {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": camada(codigo),
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "cql_filter": f"cod_imovel='{codigo}'",
    }


def _arquivo(dir_cache: Path, codigo: str) -> Path:
    return dir_cache / f"{codigo}.json"


def ler_cache(codigo: str, dir_cache: Path | None = None) -> tuple[dict, dict] | None:
    p = _arquivo(dir_cache or DIR_CACHE, codigo)
    if not p.exists():
        return None
    meta_p = p.with_suffix(".json.meta.json")
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    return json.loads(p.read_text(encoding="utf-8")), meta


def consultar(codigo: str, dir_cache: Path | None = None, cliente: httpx.Client | None = None) -> tuple[dict, dict]:
    """Resposta GeoJSON do WFS e metadados. Levanta FonteIndisponivel em falha de rede/serviço."""
    dir_cache = dir_cache or DIR_CACHE
    try:
        cli = cliente or httpx.Client(timeout=20, headers={"User-Agent": "TELLUS/0.1 (NASA Space Apps)"})
        r = cli.get(URL, params=parametros(codigo))
    except httpx.HTTPError as e:
        raise FonteIndisponivel(f"sem resposta do WFS do SICAR ({type(e).__name__})") from e
    if r.status_code >= 500:
        raise FonteIndisponivel(f"WFS do SICAR respondeu HTTP {r.status_code}")
    try:
        corpo = r.json()
    except ValueError as e:  # XML de exceção do GeoServer
        raise FonteIndisponivel(f"WFS do SICAR devolveu erro: {r.text[:160]}") from e
    if corpo.get("type") != "FeatureCollection":
        raise FonteIndisponivel("WFS do SICAR devolveu um formato inesperado")
    meta = {
        "url": str(r.url),
        "camada": camada(codigo),
        "obtido_em": dt.date.today().isoformat(),
        "status_http": r.status_code,
        "sha256": hashlib.sha256(r.content).hexdigest(),
    }
    p = _arquivo(dir_cache, codigo)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(r.content)
    p.with_suffix(".json.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return corpo, meta
