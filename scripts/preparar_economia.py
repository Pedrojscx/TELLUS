"""Gera referencias/economia/: planilhas Conab (praças 2025/2026) já lidas e a série CEPEA do milho.

Usa os XLS da Conab baixados por scripts/preparar_localizacao.py (data/raw/localizacao/) e baixa a série
do Indicador do Milho ESALQ/BM&FBovespa (CEPEA) para data/raw/economia/.
Uso: uv run --project backend python scripts/preparar_economia.py
"""

import datetime as dt
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import httpx
import xlrd

from tellus.economia import conab

RAIZ = Path(__file__).resolve().parents[1]
RAW_LOC = RAIZ / "data" / "raw" / "localizacao"
RAW = RAIZ / "data" / "raw" / "economia"
REF = RAIZ / "referencias" / "economia"
PRACAS = json.loads((RAIZ / "referencias" / "localizacao" / "pracas_conab.json").read_text(encoding="utf-8"))
CEPEA_URL = "https://www.cepea.org.br/br/indicador/series/milho.aspx?id=77"
ARQUIVOS = {"soja": "conab_soja.xls", "milho_2a_safra": "conab_milho_2a_safra.xls", "sorgo": "conab_sorgo.xls"}
APELIDOS = {("p. do leste", "MT"): "primavera do leste", ("c. novo do parecis", "MT"): "campo novo do parecis",
            ("m. candido rondon", "PR"): "marechal candido rondon", ("s. luiz gonzaga", "RS"): "sao luiz gonzaga"}


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def meta(p: Path) -> dict:
    m = p.with_name(p.name + ".meta.json")
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}


def conab_json() -> None:
    por_nome = {(norm(p["nome"]), p["uf"]): p for p in PRACAS}
    for cultura, arq in ARQUIVOS.items():
        caminho = RAW_LOC / arq
        livro = xlrd.open_workbook(caminho, on_demand=True)
        saida = {"cultura": cultura, "fonte": "Conab — custos de produção, série histórica", "arquivo": arq,
                 "url": meta(caminho).get("url"), "obtido_em": meta(caminho).get("obtido_em"),
                 "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(), "planilhas": []}
        for aba in livro.sheet_names():
            m = re.match(r"^(?:OGM-)?(.+)-([A-Z]{2})-(\d{4})$", aba.strip())
            if not m or m.group(3) not in ("2025", "2026"):
                continue
            nome, uf = norm(m.group(1)), m.group(2)
            praca = por_nome.get((APELIDOS.get((nome, uf), nome), uf))
            if praca is None:
                raise SystemExit(f"praça sem código IBGE: {aba}")
            s = livro.sheet_by_name(aba)
            p = conab.ler_aba([s.row_values(i) for i in range(s.nrows)])
            divergencias = conab.conferir(p)
            saida["planilhas"].append({"aba": aba, "ano": int(m.group(3)), "codigo_ibge": praca["codigo_ibge"],
                                       "praca": praca["nome"], "uf": uf, "lat": praca["lat"], "lon": praca["lon"],
                                       "ogm": aba.startswith("OGM-"), "divergencias": divergencias, **p})
        (REF / f"conab_{cultura}.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  conab_{cultura}.json: {len(saida['planilhas'])} planilhas")


def cepea_json() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / "cepea_milho.xls"
    r = httpx.get(CEPEA_URL, headers={"User-Agent": "Mozilla/5.0 (TELLUS)"}, timeout=120, follow_redirects=True)
    r.raise_for_status()
    p.write_bytes(r.content)
    m = {"url": CEPEA_URL, "obtido_em": dt.date.today().isoformat(), "sha256": hashlib.sha256(r.content).hexdigest()}
    p.with_name(p.name + ".meta.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    # o arquivo do CEPEA tem a tabela de alocação do OLE inconsistente; o conteúdo da planilha é íntegro
    s = xlrd.open_workbook(p, ignore_workbook_corruption=True).sheet_by_index(0)
    titulo = str(s.cell_value(0, 0)).strip()
    cab = [str(x).strip() for x in s.row_values(3)]
    if cab[:2] != ["Data", "À vista R$"]:
        raise SystemExit(f"cabeçalho inesperado no CEPEA: {cab}")
    serie = []
    for i in range(4, s.nrows):
        d, v = s.row_values(i)[:2]
        if isinstance(v, float) and str(d).count("/") == 2:
            dd, mm, aa = str(d).split("/")
            serie.append({"data": f"{aa}-{mm}-{dd}", "r_saca": round(v, 2)})
    serie = [x for x in serie if x["data"] >= "2024-01-01"]
    saida = {"indicador": titulo, "produto": "milho", "praca": "Campinas-SP (região de referência do indicador)",
             "unidade": "R$/saca de 60 kg, à vista, sem frete até a fazenda", "fonte": "Cepea/Esalq-USP",
             "url": CEPEA_URL, **m, "serie": serie}
    (REF / "cepea_milho.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  cepea_milho.json: {len(serie)} dias, último {serie[-1]}")


if __name__ == "__main__":
    REF.mkdir(parents=True, exist_ok=True)
    conab_json()
    cepea_json()
