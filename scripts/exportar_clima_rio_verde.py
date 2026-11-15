"""Exporta a série de Rio Verde-GO (célula da A025) do cache para referencias/clima/rio_verde_go/.

A exportação é derivada e versionada para que a demo rode sem rede em qualquer máquina.
"""

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

from tellus.clima import imerg, power

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "data" / "raw" / "clima"
DEST = RAIZ / "referencias" / "clima" / "rio_verde_go"
LAT, LON = -17.785278, -50.965

cel = imerg.CelulaImerg.do_ponto(LAT, LON)
linhas = imerg.ler_cache(CACHE, cel)
p_power = power.arquivo_cache(CACHE, LAT, LON)
pw = power.ler(p_power)
chave_p, _, _ = power.chave_celula(LAT, LON)
DEST.mkdir(parents=True, exist_ok=True)
campos = ["data", "chuva_mm", "imerg_contagem", "imerg_situacao", "tmax_c", "tmin_c", "radiacao_mj_m2",
          "umidade_pct", "vento_m_s", "power_chuva_mm"]
mapa = {"tmax_c": "T2M_MAX", "tmin_c": "T2M_MIN", "radiacao_mj_m2": "ALLSKY_SFC_SW_DWN", "umidade_pct": "RH2M",
        "vento_m_s": "WS2M", "power_chuva_mm": "PRECTOTCORR"}
datas = sorted(set(linhas) | set(pw["dias"]))
with (DEST / "serie_diaria.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    for d in datas:
        l = linhas.get(d, {})
        p = pw["dias"].get(d, {})
        w.writerow({"data": d, "chuva_mm": l.get("chuva_mm", ""), "imerg_contagem": l.get("contagem", ""),
                    "imerg_situacao": l.get("situacao", "fora_do_cache")}
                   | {k: ("" if p.get(v) is None else p.get(v)) for k, v in mapa.items()})
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p_imerg = imerg.arquivo_cache(CACHE, cel)
meta = {
    "local": "Rio Verde-GO, estação INMET A025",
    "imerg": {"celula": cel.chave, "centro": cel.centro, "versao": f"{imerg.PRODUTO} {imerg.VERSAO}",
              "obtido_em": max(l["obtido_em"] for l in linhas.values()), "sha256_cache": sha(p_imerg)},
    "power": {"celula": chave_p, "altitude_m": pw["altitude_m"], "fontes": pw["fontes"], "obtido_em": pw["obtido_em"],
              "url": pw["url"], "sha256_cache": sha(p_power)},
    "gerado_em": dt.date.today().isoformat(),
}
(DEST / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
(DEST / "FONTE.md").write_text(
    "# Série de clima de Rio Verde-GO (referência versionada)\n\n"
    "Gerada por `scripts/exportar_clima_rio_verde.py` a partir do cache de `scripts/baixar_imerg.py` e\n"
    "`scripts/baixar_power.py`. Metadados completos (células, versões, datas e sha256) em `meta.json`.\n\n"
    f"- Chuva: NASA GPM IMERG Final {imerg.VERSAO}, célula {cel.chave} (0,1°), via OPeNDAP DAP4 ({imerg.BASE}).\n"
    f"- Tmax, Tmin, radiação, umidade, vento: NASA POWER diário, community AG, célula {chave_p} ({power.URL}).\n"
    "- `power_chuva_mm` existe só para a comparação de fontes; não entra no cálculo (constituição 1.1.0).\n"
    "- `imerg_situacao`: ok, sem_dado, nao_publicado (granule inexistente, D-002) ou fora_do_cache.\n",
    encoding="utf-8")
print(DEST, len(datas), "dias")
