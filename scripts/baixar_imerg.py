"""Baixa a série diária IMERG Final de uma célula para o cache local (data/raw/clima/).

Uso: uv run --project backend python scripts/baixar_imerg.py [lat lon] [inicio AAAA-MM-DD]
Sem argumentos, baixa a célula da estação INMET A025 (Rio Verde-GO) desde 2001-01-01.
O token vem de EARTHDATA_TOKEN; se a variável não existir, é lida do .env sem ser exibida.
"""

import datetime as dt
import os
import sys
from pathlib import Path

from tellus.clima import imerg

RAIZ = Path(__file__).resolve().parents[1]

if "EARTHDATA_TOKEN" not in os.environ and (RAIZ / ".env").exists():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("EARTHDATA_TOKEN="):
            os.environ["EARTHDATA_TOKEN"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

lat, lon = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (-17.785278, -50.965)
inicio = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) >= 4 else imerg.INICIO_PADRAO
c = imerg.CelulaImerg.do_ponto(lat, lon)
print(f"célula {c.chave} (índices lat {c.i_lat}, lon {c.i_lon}) desde {inicio}", flush=True)
p = imerg.atualizar_cache(RAIZ / "data" / "raw" / "clima", c, inicio=inicio,
                          progresso=lambda n, t: print(f"  {n}/{t}", flush=True))
linhas = imerg.ler_cache(RAIZ / "data" / "raw" / "clima", c)
from collections import Counter
print(p, Counter(l["situacao"] for l in linhas.values()))
