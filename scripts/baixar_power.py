"""Baixa a série diária do NASA POWER (variáveis da ETo) para o cache local (data/raw/clima/power/).

Uso: uv run --project backend python scripts/baixar_power.py [lat lon]
Sem argumentos, usa a estação INMET A025 (Rio Verde-GO). Não precisa de credencial.
"""

import sys
from pathlib import Path

from tellus.clima import power

RAIZ = Path(__file__).resolve().parents[1]
lat, lon = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (-17.785278, -50.965)
p = power.baixar(RAIZ / "data" / "raw" / "clima", lat, lon)
d = power.ler(p)
print(p, len(d["dias"]), "dias; altitude da célula", d["altitude_m"], "m; fontes", d["fontes"])
