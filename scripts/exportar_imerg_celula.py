"""Versiona a chuva IMERG de UMA célula já baixada (cache de scripts/baixar_imerg.py) em referencias/clima/<nome>/.

Uso: uv run --project backend python scripts/exportar_imerg_celula.py <lat> <lon> <nome> "<descrição do local>"
Gera serie_diaria.csv (só chuva), meta.json (célula, versão, data, sha256) e FONTE.md. Só IMERG: o POWER
dessas células não é versionado aqui (a referência de Rio Verde já cobre o POWER da região).
"""

import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from tellus.clima import imerg

RAIZ = Path(__file__).resolve().parents[1]
lat, lon, nome, descricao = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3], sys.argv[4]
cel = imerg.CelulaImerg.do_ponto(lat, lon)
cache = RAIZ / "data" / "raw" / "clima"
linhas = imerg.ler_cache(cache, cel)
if not linhas:
    sys.exit(f"célula {cel.chave} sem cache; rode scripts/baixar_imerg.py {lat} {lon} antes")

destino = RAIZ / "referencias" / "clima" / nome
destino.mkdir(parents=True, exist_ok=True)
serie = destino / "serie_diaria.csv"
with serie.open("w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["data", "chuva_mm", "imerg_contagem", "imerg_situacao"])
    for d in sorted(linhas):
        l = linhas[d]
        w.writerow([d, l["chuva_mm"], l["contagem"], l["situacao"]])

ok = sorted(d for d, l in linhas.items() if l["situacao"] == "ok")
obtido = max(l["obtido_em"] for l in linhas.values())
arq_cache = next((cache / "imerg").glob(f"{cel.chave}.csv"))
meta = {
    "local": {"nome": descricao, "ponto_pedido": [lat, lon]},
    "imerg": {
        "celula": cel.chave, "centro": [float(x) for x in cel.chave.split("_")], "versao": "GPM_3IMERGDF V07B",
        "obtido_em": obtido, "periodo_ok": [ok[0], ok[-1]] if ok else None, "dias_ok": len(ok),
        "sha256_cache": hashlib.sha256(arq_cache.read_bytes()).hexdigest(),
        "sha256_serie": hashlib.sha256(serie.read_bytes()).hexdigest(),
    },
    "gerado_em": dt.date.today().isoformat(),
}
(destino / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
(destino / "FONTE.md").write_text(
    f"# Chuva IMERG da célula {cel.chave} ({descricao})\n\n"
    f"Gerada por `scripts/exportar_imerg_celula.py` a partir do cache de `scripts/baixar_imerg.py`.\n\n"
    f"- Fonte: NASA GPM IMERG Final V07B (GPM_3IMERGDF), célula {cel.chave} (0,1°), via OPeNDAP DAP4 "
    f"(https://opendap.earthdata.nasa.gov/collections/C2723754864-GES_DISC/granules/).\n"
    f"- Dias com dado: {len(ok)} ({ok[0] if ok else '-'} a {ok[-1] if ok else '-'}); obtido em {obtido}.\n"
    f"- `imerg_situacao`: ok, sem_dado ou nao_publicado (granule ainda inexistente, D-002).\n"
    f"- Só chuva. Sem POWER nesta pasta.\n",
    encoding="utf-8", newline="\n")
print(destino, cel.chave, len(ok), "dias ok")
