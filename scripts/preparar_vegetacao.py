"""Prepara o cache de vegetação MODIS (spec 009) a partir da ORNL DAAC MODIS Web Service.

Uso (com internet; não precisa de login):
    cd backend && uv run python ../scripts/preparar_vegetacao.py --lat -17.785278 --lon -50.965 --meses 12
    ... --exportar-referencia rio_verde_go   # copia a série derivada para referencias/vegetacao/series/

Grava:
  data/raw/vegetacao/<chave_area>/bruto/<PRODUTO>_<banda>_<ini>_<fim>.json  (respostas brutas, fora do Git)
  data/raw/vegetacao/<chave_area>/bruto/<...>.json.meta.json                 (url, obtido_em, sha256)
  data/raw/vegetacao/<chave_area>/<PRODUTO>.csv + .meta.json                (série por pixel lida pelo serviço)

Só ponto (um pixel de 250 m). Polígono e HLS: ver specs/009-vegetacao-modis-hls/plan.md.
HLS não é baixado aqui: exige Earthdata login e leitura de GeoTIFF (COG), dependência que o
backend ainda não tem.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend" / "src"))

from tellus.vegetacao import modis_ornl, regras, servico  # noqa: E402


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--produto", default="MOD13Q1", choices=["MOD13Q1", "MYD13Q1"])
    ap.add_argument("--meses", type=int, default=12, help="janela a partir da última composição publicada")
    ap.add_argument("--exportar-referencia", metavar="NOME", help="copia a série para referencias/vegetacao/series/")
    a = ap.parse_args()

    chave = servico.chave_ponto(a.lat, a.lon)
    pasta = servico.RAIZ / "data" / "raw" / "vegetacao" / chave
    bruto = pasta / "bruto"
    bruto.mkdir(parents=True, exist_ok=True)
    hoje = dt.date.today().isoformat()
    cli = modis_ornl._cliente()

    url = modis_ornl.url_datas(a.produto, a.lat, a.lon)
    datas_js, raw = modis_ornl.obter(url, cli)
    (bruto / f"{a.produto}_datas.json").write_bytes(raw)
    (bruto / f"{a.produto}_datas.json.meta.json").write_text(
        json.dumps({"url": url, "obtido_em": hoje, "sha256": _sha(raw)}, indent=1), encoding="utf-8")
    todas = sorted(datas_js["dates"], key=lambda d: d["calendar_date"])
    ultima = dt.date.fromisoformat(todas[-1]["calendar_date"])
    corte = ultima - dt.timedelta(days=round(a.meses * 365.25 / 12))
    alvo = [d for d in todas if dt.date.fromisoformat(d["calendar_date"]) > corte]
    print(f"{a.produto}: {len(todas)} datas publicadas; última {ultima}; {len(alvo)} na janela de {a.meses} meses")

    valores: dict[str, dict[str, dict[str, int]]] = {}  # data -> pixel -> banda -> valor
    consultas = []
    for i in range(0, len(alvo), modis_ornl.MAX_DATAS):
        bloco = alvo[i:i + modis_ornl.MAX_DATAS]
        ini, fim = bloco[0]["modis_date"], bloco[-1]["modis_date"]
        for nome, banda in modis_ornl.BANDAS.items():
            url = modis_ornl.url_subset(a.produto, a.lat, a.lon, banda, ini, fim)
            js, raw = modis_ornl.obter(url, cli)
            arq = bruto / f"{a.produto}_{nome}_{ini}_{fim}.json"
            arq.write_bytes(raw)
            arq.with_name(arq.name + ".meta.json").write_text(
                json.dumps({"url": url, "obtido_em": hoje, "sha256": _sha(raw)}, indent=1), encoding="utf-8")
            consultas.append(url)
            cs, nrows, ncols = float(js["cellsize"]), int(js["nrows"]), int(js["ncols"])
            xll, yll = float(js["xllcorner"]), float(js["yllcorner"])
            for s in js["subset"]:
                for k, v in enumerate(s["data"]):
                    r, c = divmod(k, ncols)
                    x = xll + (c + 0.5) * cs
                    y = yll + (nrows - r - 0.5) * cs
                    px = regras.pixel_de_xy(x, y, servico.GRADE)
                    valores.setdefault(s["calendar_date"], {}).setdefault(px, {})[nome] = int(v)
            print(f"  {nome} {ini}–{fim}: ok")
    cli.close()

    px_ponto = regras.pixel_senoidal(a.lat, a.lon, servico.GRADE)
    pixels = {p for d in valores.values() for p in d}
    if px_ponto not in pixels:
        print(f"AVISO: pixel calculado {px_ponto} não está entre os devolvidos {sorted(pixels)}")
    p_csv = pasta / f"{a.produto}.csv"
    with p_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["data", "pixel", "ndvi", "evi", "pixel_reliability", "vi_quality"])
        for d in sorted(valores):
            for p in sorted(valores[d]):
                b = valores[d][p]
                w.writerow([d, p, b.get("ndvi", ""), b.get("evi", ""), b.get("pixel_reliability", ""), b.get("vi_quality", "")])
    meta = {
        "produto": a.produto, "versao": "061", "sintetico": False, "obtido_em": hoje,
        "consulta": f"ORNL DAAC MODIS Web Service ({modis_ornl.BASE}); {len(consultas)} pedidos; ponto {a.lat}, {a.lon}",
        "urls": consultas, "sha256": _sha(p_csv.read_bytes()), "pesos": {px_ponto: 1.0},
    }
    (pasta / f"{a.produto}.meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8")
    print(f"série gravada em {p_csv} ({len(valores)} composições)")

    if a.exportar_referencia:
        destino = servico.DIR_SERIES / chave
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy(p_csv, destino / p_csv.name)
        shutil.copy(pasta / f"{a.produto}.meta.json", destino / f"{a.produto}.meta.json")
        (destino / "NOME").write_text(a.exportar_referencia + "\n", encoding="utf-8")
        print(f"referência versionada em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
