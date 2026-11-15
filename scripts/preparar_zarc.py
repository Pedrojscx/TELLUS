"""Baixa os relatórios SISZARC de uma ou mais UFs e gera referencias/zarc/<safra>/<UF>.json.

Uso: uv run --project backend python scripts/preparar_zarc.py GO [MT MS ...]
Os XLS brutos ficam em data/raw/zarc/siszarc/ (fora do Git) com .meta.json.
"""

import datetime as dt
import hashlib
import json
import sys
import unicodedata
import re
from pathlib import Path

from tellus.zarc import regras, siszarc

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw" / "zarc" / "siszarc"
CULT = json.loads((RAIZ / "referencias" / "zarc" / "culturas.json").read_text(encoding="utf-8"))
MUN = json.loads((RAIZ / "referencias" / "localizacao" / "municipios.json").read_text(encoding="utf-8"))


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def gerar(uf: str) -> None:
    safra = CULT["safra_vigente"]
    por_nome = {norm(m["nome"]): m["codigo_ibge"] for m in MUN if m["uf"] == uf}
    saida = {"safra": safra, "uf": uf, "manejo": CULT["manejo"], "gerado_em": dt.date.today().isoformat(),
             "conjuntos": [], "municipios": {}}
    sem_ibge = set()
    for chave, c in CULT["culturas"].items():
        caminhos = siszarc.baixar_relatorios(RAW, safra, c["codigo_siszarc"], uf)
        print(f"  {uf} {chave}: {len(caminhos)} relatório(s)", flush=True)
        for p in caminhos:
            meta = json.loads(p.with_suffix(".xls.meta.json").read_text(encoding="utf-8"))
            linhas = siszarc.ler_relatorio(p.read_bytes())
            if not linhas:
                continue
            l0 = linhas[0]
            saida["conjuntos"].append({
                "cultura": chave, "nome_siszarc": l0["cultura"], "portaria": l0["portaria"],
                "data_portaria": l0["data_portaria"], "grupo": l0["grupo"], "safra": l0["safra"],
                "obtido_em": meta["obtido_em"], "arquivo": p.name, "sha256": meta["sha256"], "linhas": len(linhas),
            })
            for l in linhas:
                ibge = por_nome.get(norm(l["municipio"]))
                if not ibge:
                    sem_ibge.add(l["municipio"])
                    continue
                (saida["municipios"].setdefault(ibge, {}).setdefault(chave, {})
                 .setdefault(l["grupo"], {}))[l["solo"]] = {"riscos": regras.codificar(l["riscos"]), "portaria": l["portaria"]}
    if sem_ibge:
        sys.exit(f"ERRO: municípios do SISZARC sem código IBGE em {uf}: {sorted(sem_ibge)}")
    dest = RAIZ / "referencias" / "zarc" / safra.replace(" / ", "-") / f"{uf}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {dest.name}: {len(saida['municipios'])} municípios, {len(saida['conjuntos'])} conjuntos")


if __name__ == "__main__":
    for uf in sys.argv[1:] or ["GO"]:
        gerar(uf.upper())
