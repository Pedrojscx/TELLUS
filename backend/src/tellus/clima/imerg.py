"""Cliente do IMERG Final V07 diário (GPM_3IMERGDF) via OPeNDAP DAP4 da NASA.

Baixa uma célula de 0,1° por dia e guarda num CSV por célula (cache retomável). A credencial vem
só da variável de ambiente EARTHDATA_TOKEN (Princípio VIII) e nunca é gravada nem exibida.
"""

from __future__ import annotations

import concurrent.futures as cf
import csv
import datetime as dt
import io
import math
import os
from dataclasses import dataclass
from pathlib import Path

import h5py
import httpx

COLECAO = "C2723754864-GES_DISC"
PRODUTO = "GPM_3IMERGDF"
VERSAO = "V07B"
BASE = f"https://opendap.earthdata.nasa.gov/collections/{COLECAO}/granules/"
INICIO_PADRAO = dt.date(2001, 1, 1)
CAMPOS = ["data", "chuva_mm", "contagem", "situacao", "obtido_em"]


@dataclass(frozen=True)
class CelulaImerg:
    i_lat: int
    i_lon: int

    @classmethod
    def do_ponto(cls, lat: float, lon: float) -> "CelulaImerg":
        return cls(math.floor(round((lat + 90) / 0.1, 9)), math.floor(round((lon + 180) / 0.1, 9)))

    @property
    def centro(self) -> tuple[float, float]:
        return round(-90 + (self.i_lat + 0.5) * 0.1, 4), round(-180 + (self.i_lon + 0.5) * 0.1, 4)

    @property
    def chave(self) -> str:
        lat, lon = self.centro
        return f"{lat:+.2f}_{lon:+.2f}"


def url_dia(d: dt.date) -> str:
    nome = f"3B-DAY.MS.MRG.3IMERG.{d:%Y%m%d}-S000000-E235959.{VERSAO}.nc4"
    return f"{BASE}{PRODUTO}.07%3A{nome}.dap.nc4"


def restricao(c: CelulaImerg) -> str:
    sel = f"[0:1:0][{c.i_lon}:1:{c.i_lon}][{c.i_lat}:1:{c.i_lat}]"
    return f"precipitation{sel};precipitation_cnt{sel};lat[{c.i_lat}:1:{c.i_lat}];lon[{c.i_lon}:1:{c.i_lon}]"


def _token() -> str:
    tok = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not tok:
        raise RuntimeError("EARTHDATA_TOKEN não definido no ambiente; a chuva IMERG não pode ser baixada.")
    return tok


def _baixar_dia(cliente: httpx.Client, c: CelulaImerg, d: dt.date) -> dict:
    hoje = dt.date.today().isoformat()
    for _ in range(3):
        try:
            r = cliente.get(url_dia(d), params={"dap4.ce": restricao(c)})
        except httpx.HTTPError:
            continue
        if r.status_code == 404:
            return {"data": d.isoformat(), "chuva_mm": "", "contagem": "", "situacao": "nao_publicado", "obtido_em": hoje}
        if r.status_code == 200 and r.content[:4] == b"\x89HDF":
            with h5py.File(io.BytesIO(r.content), "r") as f:
                valor = float(f["precipitation"][()].ravel()[0])
                cont = int(f["precipitation_cnt"][()].ravel()[0])
            valido = math.isfinite(valor) and valor >= 0 and cont > 0
            return {
                "data": d.isoformat(),
                "chuva_mm": f"{valor:.4f}" if valido else "",
                "contagem": cont,
                "situacao": "ok" if valido else "sem_dado",
                "obtido_em": hoje,
            }
        if r.status_code in (401, 403):
            raise RuntimeError(f"Earthdata recusou o acesso (HTTP {r.status_code}). Confira o token e a autorização GES DISC.")
    return {"data": d.isoformat(), "chuva_mm": "", "contagem": "", "situacao": "falha_rede", "obtido_em": hoje}


def arquivo_cache(dir_cache: Path, c: CelulaImerg) -> Path:
    return dir_cache / "imerg" / f"{c.chave}.csv"


def ler_cache(dir_cache: Path, c: CelulaImerg) -> dict[str, dict]:
    p = arquivo_cache(dir_cache, c)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as f:
        return {linha["data"]: linha for linha in csv.DictReader(f)}


def atualizar_cache(
    dir_cache: Path,
    c: CelulaImerg,
    inicio: dt.date = INICIO_PADRAO,
    fim: dt.date | None = None,
    trabalhadores: int = 16,
    progresso=None,
) -> Path:
    """Baixa os dias que faltam (ou falharam) e regrava o CSV da célula em ordem de data."""
    fim = fim or dt.date.today()
    existentes = ler_cache(dir_cache, c)
    refazer = {"falha_rede"}
    dias = [
        inicio + dt.timedelta(days=i)
        for i in range((fim - inicio).days + 1)
        if existentes.get((inicio + dt.timedelta(days=i)).isoformat(), {}).get("situacao", "falha_rede") in refazer
    ]
    p = arquivo_cache(dir_cache, c)
    p.parent.mkdir(parents=True, exist_ok=True)
    if dias:
        with httpx.Client(headers={"Authorization": f"Bearer {_token()}"}, timeout=60, follow_redirects=True) as cli:
            with cf.ThreadPoolExecutor(trabalhadores) as ex:
                for n, linha in enumerate(ex.map(lambda d: _baixar_dia(cli, c, d), dias), 1):
                    existentes[linha["data"]] = linha
                    if progresso and n % 500 == 0:
                        progresso(n, len(dias))
                        _gravar(p, existentes)
    _gravar(p, existentes)
    return p


def _gravar(p: Path, linhas: dict[str, dict]) -> None:
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for k in sorted(linhas):
            w.writerow({c: linhas[k].get(c, "") for c in CAMPOS})
    tmp.replace(p)
