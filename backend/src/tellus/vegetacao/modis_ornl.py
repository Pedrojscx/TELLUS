"""Cliente da ORNL DAAC MODIS Web Service (sem login): datas e recortes de MOD13Q1/MYD13Q1 v061.

Documentação: https://modis.ornl.gov/data/modis_webservice.html
A API devolve no máximo 10 datas por pedido e valores brutos (inteiros) por pixel da grade senoidal.
Só o script de preparação usa este módulo; o serviço da API lê apenas o cache.
"""

from __future__ import annotations

import httpx

BASE = "https://modis.ornl.gov/rst/api/v1"
BANDAS = {
    "ndvi": "250m_16_days_NDVI",
    "evi": "250m_16_days_EVI",
    "pixel_reliability": "250m_16_days_pixel_reliability",
    "vi_quality": "250m_16_days_VI_Quality",
}
MAX_DATAS = 10


def _cliente() -> httpx.Client:
    return httpx.Client(timeout=180, headers={"Accept": "application/json", "User-Agent": "tellus-prototipo"})


def url_datas(produto: str, lat: float, lon: float) -> str:
    return f"{BASE}/{produto}/dates?latitude={lat}&longitude={lon}"


def url_subset(produto: str, lat: float, lon: float, banda: str, ini: str, fim: str, km: int = 0) -> str:
    return (
        f"{BASE}/{produto}/subset?latitude={lat}&longitude={lon}&band={banda}"
        f"&startDate={ini}&endDate={fim}&kmAboveBelow={km}&kmLeftRight={km}"
    )


def obter(url: str, cliente: httpx.Client | None = None, tentativas: int = 3) -> tuple[dict, bytes]:
    cli = cliente or _cliente()
    erro: Exception | None = None
    try:
        for _ in range(tentativas):
            try:
                r = cli.get(url)
                r.raise_for_status()
                return r.json(), r.content
            except httpx.HTTPError as e:  # rede instável: tenta de novo
                erro = e
        raise RuntimeError(f"ORNL DAAC MODIS Web Service indisponível: {erro}")
    finally:
        if cliente is None:
            cli.close()
