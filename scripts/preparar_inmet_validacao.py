"""Chuva diária de uma estação automática do INMET, a partir dos arquivos anuais do portal, para a validação local.

Uso: uv run --project backend python scripts/preparar_inmet_validacao.py <codigo> <ano> [<ano> ...]
Lê data/raw/inmet_historico/<ano>.zip (https://portal.inmet.gov.br/uploads/dadoshistoricos/<ano>.zip, sem login)
e grava referencias/clima_inmet/<codigo>/ (serie_diaria.csv, meta.json, FONTE.md).

Método igual ao da A025 (docs/pesquisa_chuva/RELATORIO.md, item 2): o dia UTC D soma os registros horários de
01:00 de D até 00:00 de D+1 e só vale com 24 horas válidas. Hora vazia ou -9999 é ausente, nunca zero.
"""

import csv
import datetime as dt
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "data" / "raw" / "inmet_historico"
URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"

codigo, anos = sys.argv[1].upper(), [int(a) for a in sys.argv[2:]]
horas: dict[dt.datetime, float | None] = {}
cabecalho: dict[str, str] = {}
arquivos = []
for ano in anos:
    z = ORIGEM / f"{ano}.zip"
    nomes = [n for n in zipfile.ZipFile(z).namelist() if f"_{codigo}_" in n.upper() and n.upper().endswith(".CSV")]
    if not nomes:
        sys.exit(f"{codigo} não está em {z.name}")
    texto = zipfile.ZipFile(z).read(nomes[0]).decode("latin-1")
    linhas = texto.splitlines()
    for l in linhas[:8]:
        k, _, v = l.partition(":;")
        cabecalho[k.strip()] = v.strip()
    arquivos.append({"ano": ano, "zip": z.name, "arquivo": nomes[0], "url": URL.format(ano=ano),
                     "sha256_zip": hashlib.sha256(z.read_bytes()).hexdigest()})
    leitor = csv.reader(io.StringIO("\n".join(linhas[8:])), delimiter=";")
    next(leitor)  # nomes das colunas; a chuva horária é a 3ª coluna
    for r in leitor:
        if len(r) < 3 or not r[0]:
            continue
        data = dt.datetime.strptime(r[0].replace("-", "/"), "%Y/%m/%d")
        hora = int(r[1].split()[0][:2]) if " UTC" in r[1] else int(r[1][:2])
        v = r[2].replace(",", ".").strip()
        horas[data + dt.timedelta(hours=hora)] = None if v in ("", "-9999") else float(v)

ini, fim = min(horas).date(), max(horas).date()
saida = []
d = ini
while d <= fim:
    regs = [horas.get(dt.datetime.combine(d, dt.time()) + dt.timedelta(hours=h)) for h in range(1, 25)]
    validas = [v for v in regs if v is not None]
    saida.append((d.isoformat(), len(validas), f"{sum(validas):.1f}" if len(validas) == 24 else ""))
    d += dt.timedelta(days=1)

lat = float(cabecalho["LATITUDE"].replace(",", "."))
lon = float(cabecalho["LONGITUDE"].replace(",", "."))
destino = RAIZ / "referencias" / "clima_inmet" / codigo
destino.mkdir(parents=True, exist_ok=True)
serie = destino / "serie_diaria.csv"
with serie.open("w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["data", "horas_validas", "chuva_mm"])
    w.writerows(saida)
completos = sum(1 for s in saida if s[2] != "")
meta = {
    "estacao": {"codigo": codigo, "nome": cabecalho.get("ESTACAO"), "uf": cabecalho.get("UF"), "lat": lat, "lon": lon,
                "altitude_m": float(cabecalho["ALTITUDE"].replace(",", ".")) if cabecalho.get("ALTITUDE") else None},
    "fonte": "INMET, estação automática (dados históricos anuais do portal)",
    "arquivos": arquivos,
    "metodo": "dia UTC D = soma das horas de 01:00 de D a 00:00 de D+1; só com 24 horas válidas (docs/pesquisa_chuva/RELATORIO.md)",
    "periodo": [ini.isoformat(), fim.isoformat()], "dias_completos": completos, "dias_total": len(saida),
    "obtido_em": dt.date.today().isoformat(),
    "sha256_serie": hashlib.sha256(serie.read_bytes()).hexdigest(),
}
(destino / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
(destino / "FONTE.md").write_text(
    f"# Chuva diária INMET {codigo} ({cabecalho.get('ESTACAO')}-{cabecalho.get('UF')})\n\n"
    f"Gerada por `scripts/preparar_inmet_validacao.py` a partir dos arquivos anuais do portal do INMET "
    f"({', '.join(a['url'] for a in arquivos)}).\n\n"
    f"- Estação em {lat}, {lon}. Período {ini} a {fim}: {completos} de {len(saida)} dias com 24 horas válidas.\n"
    f"- Usada só para conferir a chuva de satélite (validação local). Nunca entra no cálculo.\n"
    f"- Método: {meta['metodo']}.\n",
    encoding="utf-8", newline="\n")
print(destino, f"{completos}/{len(saida)} dias completos", ini, fim)
