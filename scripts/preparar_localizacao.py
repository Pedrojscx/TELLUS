"""Prepara as referências da spec 001 (localização).

Baixa as fontes oficiais para data/raw/localizacao/ (fora do Git, com .meta.json) e gera os
arquivos derivados e versionados em referencias/localizacao/.

Uso (na raiz do repositório):
    uv run --project backend python scripts/preparar_localizacao.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import httpx
import xlrd

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw" / "localizacao"
REF = RAIZ / "referencias" / "localizacao"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
HOJE = dt.date.today().isoformat()

IBGE = "https://servicodados.ibge.gov.br/api"
CONAB = (
    "https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/"
    "arquivos-custo-de-producao/agricolas"
)

FONTES = {
    "municipios.json": (
        f"{IBGE}/v1/localidades/municipios?view=nivelado",
        "IBGE — API de localidades v1 (municípios)",
    ),
    "malha_municipios.geojson": (
        f"{IBGE}/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson"
        "&qualidade=minima&intrarregiao=municipio",
        "IBGE — API de malhas v3, municípios, qualidade mínima",
    ),
    "brasil.geojson": (
        f"{IBGE}/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima",
        "IBGE — API de malhas v3, contorno do país, qualidade mínima",
    ),
    "estacoes_inmet.json": (
        "https://apitempo.inmet.gov.br/estacoes/T",
        "INMET — catálogo de estações automáticas",
    ),
    "conab_soja.xls": (
        f"{CONAB}/serie-historica-custos-soja-1997-a-2026.xls",
        "Conab — série histórica de custos de produção, soja",
    ),
    "conab_milho_2a_safra.xls": (
        f"{CONAB}/milho/milho_2a_safra_serie_historica_2005-2026.xls",
        "Conab — série histórica de custos de produção, milho 2ª safra",
    ),
    "conab_sorgo.xls": (
        f"{CONAB}/seriehistoricacustossorgo2013a2026.xls",
        "Conab — série histórica de custos de produção, sorgo",
    ),
}

ANOS_CONAB = {2025, 2026}

# Abreviações usadas nos nomes das abas da Conab -> nome oficial do IBGE.
APELIDOS_CONAB = {
    ("p. do leste", "MT"): "primavera do leste",
    ("c. novo do parecis", "MT"): "campo novo do parecis",
    ("m. candido rondon", "PR"): "marechal candido rondon",
    ("s. luiz gonzaga", "RS"): "sao luiz gonzaga",
}


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def baixar(nome: str) -> Path:
    url, _ = FONTES[nome]
    RAW.mkdir(parents=True, exist_ok=True)
    destino = RAW / nome
    resp = httpx.get(url, headers={"User-Agent": UA}, timeout=120, follow_redirects=True)
    resp.raise_for_status()
    if nome.endswith(".xls") and resp.content[:8].startswith(b"<!DOC"):
        sys.exit(f"ERRO: {nome} veio como HTML, não planilha ({url})")
    destino.write_bytes(resp.content)
    meta = {
        "url": url,
        "obtido_em": HOJE,
        "status_http": resp.status_code,
        "bytes": len(resp.content),
        "sha256": hashlib.sha256(resp.content).hexdigest(),
    }
    (RAW / f"{nome}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  {nome}: {len(resp.content):,} bytes")
    return destino


def ler_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def escrever_json(nome: str, dados) -> None:
    (REF / nome).write_text(
        json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


# --- geometria simples (mesma lógica de tellus.localizacao.regras, sem importar o backend) ---


def aneis_externos(geom: dict) -> list[list[list[float]]]:
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        return [p[0] for p in geom["coordinates"]]
    raise ValueError(geom["type"])


def centroide(geom: dict) -> tuple[float, float]:
    """Centroide ponderado por área (fórmula do polígono) dos anéis externos."""
    a_tot = cx_tot = cy_tot = 0.0
    for anel in aneis_externos(geom):
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(anel, anel[1:]):
            cruz = x0 * y1 - x1 * y0
            a += cruz
            cx += (x0 + x1) * cruz
            cy += (y0 + y1) * cruz
        if a == 0:
            continue
        a_tot += a / 2
        cx_tot += cx / 6
        cy_tot += cy / 6
    return round(cy_tot / a_tot, 5), round(cx_tot / a_tot, 5)


def bbox(geom: dict) -> list[float]:
    xs = [x for anel in aneis_externos(geom) for x, _ in anel]
    ys = [y for anel in aneis_externos(geom) for _, y in anel]
    return [min(xs), min(ys), max(xs), max(ys)]


def gerar_municipios() -> dict[str, dict]:
    lista = ler_json(RAW / "municipios.json")
    malha = ler_json(RAW / "malha_municipios.geojson")
    geoms = {f["properties"]["codarea"]: f["geometry"] for f in malha["features"]}
    saida = []
    sem_poligono = []
    for m in lista:
        cod = str(m["municipio-id"])
        item = {
            "codigo_ibge": cod,
            "nome": m["municipio-nome"],
            "uf": m["UF-sigla"],
            "nome_normalizado": normalizar(m["municipio-nome"]),
        }
        g = geoms.get(cod)
        if g:
            lat, lon = centroide(g)
            item["centroide"] = {"lat": lat, "lon": lon}
            item["bbox"] = bbox(g)
            item["tem_poligono"] = True
        else:
            # Município novo ainda sem polígono na malha (ex.: Boa Esperança do Norte-MT, 5101837).
            # Fica na lista, sem coordenada, e fora da busca e da resolução por ponto.
            item["centroide"] = None
            item["bbox"] = None
            item["tem_poligono"] = False
            sem_poligono.append(f"{item['nome']}-{item['uf']} ({cod})")
        saida.append(item)
    saida.sort(key=lambda x: x["codigo_ibge"])
    escrever_json("municipios.json", saida)
    escrever_json("malha_municipios.geojson", malha)
    escrever_json("brasil.geojson", ler_json(RAW / "brasil.geojson"))
    print(f"  municípios: {len(saida)}; polígonos: {len(geoms)}; sem polígono: {sem_poligono}")
    return {m["codigo_ibge"]: m for m in saida}


def gerar_estacoes() -> None:
    brutas = ler_json(RAW / "estacoes_inmet.json")
    saida = []
    for e in brutas:
        if e.get("TP_ESTACAO") != "Automatica":
            continue
        if not e.get("VL_LATITUDE") or not e.get("VL_LONGITUDE"):
            continue
        saida.append(
            {
                "codigo": e["CD_ESTACAO"],
                "nome": e["DC_NOME"].strip(),
                "uf": e["SG_ESTADO"],
                "lat": round(float(e["VL_LATITUDE"]), 6),
                "lon": round(float(e["VL_LONGITUDE"]), 6),
                "altitude_m": round(float(e["VL_ALTITUDE"]), 2) if e.get("VL_ALTITUDE") else None,
                "situacao": e["CD_SITUACAO"],
                "inicio_operacao": (e.get("DT_INICIO_OPERACAO") or "")[:10] or None,
            }
        )
    saida.sort(key=lambda x: x["codigo"])
    escrever_json("estacoes_inmet.json", saida)
    oper = sum(1 for e in saida if e["situacao"] == "Operante")
    print(f"  estações automáticas: {len(saida)} ({oper} operantes)")


def gerar_pracas(municipios: dict[str, dict]) -> None:
    por_nome_uf = {(m["nome_normalizado"], m["uf"]): m for m in municipios.values()}
    culturas = {
        "soja": "conab_soja.xls",
        "milho_2a_safra": "conab_milho_2a_safra.xls",
        "sorgo": "conab_sorgo.xls",
    }
    padrao = re.compile(r"^(?:OGM-)?(.+)-([A-Z]{2})-(\d{4})$")
    pracas: dict[str, dict] = {}
    falhas = []
    for cultura, arq in culturas.items():
        livro = xlrd.open_workbook(RAW / arq, on_demand=True)
        for aba in livro.sheet_names():
            m = padrao.match(aba.strip())
            if not m:
                continue
            nome, uf, ano = m.group(1).strip(), m.group(2), int(m.group(3))
            if ano not in ANOS_CONAB:
                continue
            chave = normalizar(nome)
            chave = APELIDOS_CONAB.get((chave, uf), chave)
            mun = por_nome_uf.get((chave, uf))
            if not mun:
                falhas.append(f"{aba} ({cultura})")
                continue
            p = pracas.setdefault(
                mun["codigo_ibge"],
                {
                    "codigo_ibge": mun["codigo_ibge"],
                    "nome": mun["nome"],
                    "uf": uf,
                    "lat": mun["centroide"]["lat"],
                    "lon": mun["centroide"]["lon"],
                    "culturas": {c: [] for c in culturas},
                    "abas": [],
                },
            )
            if ano not in p["culturas"][cultura]:
                p["culturas"][cultura].append(ano)
                p["culturas"][cultura].sort()
            p["abas"].append(f"{arq}:{aba}")
    if falhas:
        sys.exit("ERRO: praças Conab sem código IBGE (acrescente em APELIDOS_CONAB): " + "; ".join(falhas))
    saida = sorted(pracas.values(), key=lambda x: x["codigo_ibge"])
    escrever_json("pracas_conab.json", saida)
    resumo = {c: sum(1 for p in saida if p["culturas"][c]) for c in culturas}
    print(f"  praças Conab: {len(saida)}; por cultura: {resumo}")


def gerar_limites() -> None:
    limites = {
        "estacao_distante_km": {
            "valor": 50,
            "unidade": "km",
            "status": "hipotese",
            "motivo": "comparação de chuva grade × estação só faz sentido com a estação perto (spec 001)",
        },
        "divisa_km": {
            "valor": 2,
            "unidade": "km",
            "status": "hipotese",
            "motivo": "malha IBGE de qualidade mínima simplifica as divisas (research R2)",
        },
    }
    (REF / "limites.json").write_text(
        json.dumps(limites, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def gerar_fonte_md() -> None:
    linhas = [
        "# Fontes das referências de localização",
        "",
        "Gerado por `scripts/preparar_localizacao.py`. Os arquivos brutos ficam em",
        "`data/raw/localizacao/` (fora do Git), cada um com `.meta.json` (url, data, sha256).",
        "",
        "| Arquivo bruto | Fonte | URL | Obtido em |",
        "|---|---|---|---|",
    ]
    for nome, (url, fonte) in FONTES.items():
        meta = ler_json(RAW / f"{nome}.meta.json")
        linhas.append(f"| {nome} | {fonte} | {url} | {meta['obtido_em']} |")
    linhas += [
        "",
        "Derivados neste diretório:",
        "- `municipios.json`: lista IBGE + centroide e bbox calculados do polígono da malha.",
        "  Municípios sem polígono na malha mínima ficam com `centroide: null` e não são resolvidos.",
        "- `malha_municipios.geojson`, `brasil.geojson`: cópia da malha IBGE (qualidade mínima).",
        "- `estacoes_inmet.json`: estações automáticas, com situação (Operante/Pane).",
        "- `pracas_conab.json`: praças com planilha de custo de 2025 ou 2026 (soja, milho 2ª safra,",
        "  sorgo), ligadas ao código IBGE; coordenada = centroide do município.",
        "- `limites.json`: limites de aviso, marcados como hipótese.",
        "",
        f"versao_referencias: {HOJE}",
    ]
    (REF / "FONTE.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    REF.mkdir(parents=True, exist_ok=True)
    print("Baixando fontes:")
    for nome in FONTES:
        baixar(nome)
    print("Gerando referências:")
    municipios = gerar_municipios()
    gerar_estacoes()
    gerar_pracas(municipios)
    gerar_limites()
    gerar_fonte_md()
    print("ok")


if __name__ == "__main__":
    main()
