"""Cliente SMAP (NSIDC DAAC) e cache por célula.

- A busca de grânulos usa o CMR da NASA, que é público.
- O download do arquivo HDF5 exige `EARTHDATA_TOKEN`, lido só do ambiente (Princípio VIII). O token
  nunca é gravado, exibido ou devolvido.
- Cada célula fica num CSV em `<dir_cache>/<PRODUTO>/<grade>_r<linha>_c<coluna>.csv`, ao lado de
  `<PRODUTO>/<PRODUTO>.meta.json` (versão e unidade lidas do arquivo, URL, data de obtenção e `sintetico`).

O produto escolhido continua pendente (D-008, #70). O cliente aceita qualquer produto da ficha.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
from pathlib import Path

import h5py
import httpx

CMR_GRANULOS = "https://cmr.earthdata.nasa.gov/search/granules.json"
OPENDAP = "https://opendap.earthdata.nasa.gov"
CAMPOS = ["chave", "periodo_inicio", "periodo_fim", "variante", "valor", "qualidade", "situacao",
          "linha_arquivo", "coluna_arquivo", "granulo", "obtido_em"]


class FonteIndisponivel(Exception):
    """A NSIDC/CMR não respondeu (rede, 5xx, autenticação)."""


# ---------------------------------------------------------------- cache


def arquivo_cache(dir_cache: Path, produto: str, grade: str, linha: int, coluna: int) -> Path:
    return Path(dir_cache) / produto / f"{grade}_r{linha}_c{coluna}.csv"


def arquivo_meta(dir_cache: Path, produto: str) -> Path:
    return Path(dir_cache) / produto / f"{produto}.meta.json"


def ler_cache(dir_cache: Path, produto: str, grade: str, linha: int, coluna: int) -> tuple[list[dict], dict] | None:
    p = arquivo_cache(dir_cache, produto, grade, linha, coluna)
    m = arquivo_meta(dir_cache, produto)
    if not p.exists() or not m.exists():
        return None
    with p.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    return linhas, json.loads(m.read_text(encoding="utf-8"))


def gravar_cache(dir_cache: Path, produto: str, grade: str, linha: int, coluna: int,
                 registros: list[dict], meta: dict) -> Path:
    """Mescla registros novos (chave+variante) e grava ordenado: o mesmo cache dá a mesma resposta."""
    p = arquivo_cache(dir_cache, produto, grade, linha, coluna)
    p.parent.mkdir(parents=True, exist_ok=True)
    atuais = {}
    if p.exists():
        with p.open(encoding="utf-8", newline="") as f:
            atuais = {(r["chave"], r["variante"]): r for r in csv.DictReader(f)}
    for r in registros:
        atuais[(r["chave"], r["variante"])] = {c: r.get(c, "") for c in CAMPOS}
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for k in sorted(atuais):
            w.writerow(atuais[k])
    arquivo_meta(dir_cache, produto).write_text(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return p


# ---------------------------------------------------------------- leitura do HDF5


def _texto(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if hasattr(v, "tolist"):
        v = v.tolist()
        if isinstance(v, list):
            v = v[0] if v else None
        return _texto(v)
    return str(v)


def extrair_celula(h5: h5py.File, ficha: dict, variante: str, linha: int, coluna: int, recorte: bool = False) -> dict:
    """Valor, qualidade e índices da célula num grânulo já aberto. Não procura células vizinhas.

    `recorte=True`: o arquivo é um recorte OPeNDAP de 1×1 célula; os índices continuam conferidos
    pelos `EASE_row_index`/`EASE_column_index` do próprio arquivo.
    """
    vars_ = ficha["variaveis"][variante]
    i, j = (0, 0) if recorte else (linha, coluna)
    ds = h5[vars_["valor"]]
    valor = float(ds[i, j])
    unidade = _texto(ds.attrs.get("units"))
    qual = None
    if vars_.get("qualidade") and vars_["qualidade"] in h5:
        qual = int(h5[vars_["qualidade"]][i, j])
    lin_arq = col_arq = None
    if vars_.get("linha") and vars_["linha"] in h5:
        lin_arq = int(h5[vars_["linha"]][i, j])
        col_arq = int(h5[vars_["coluna"]][i, j])
        fill_idx = ficha.get("fill_qualidade")
        if lin_arq != fill_idx and (lin_arq, col_arq) != (linha, coluna):
            raise ValueError(f"índice da grade não confere: calculado {(linha, coluna)}, arquivo {(lin_arq, col_arq)}")
    return {"valor": valor, "qualidade": qual, "unidade_no_arquivo": unidade,
            "linha_arquivo": lin_arq, "coluna_arquivo": col_arq}


def registro(ficha: dict, variante: str, granulo: dict, extraido: dict, obtido_em: str) -> dict:
    v = extraido["valor"]
    fill = ficha["fill_valor"]
    situacao = "ok" if (v == v and v != fill and v >= 0) else "sem_dado"
    return {
        "chave": granulo["inicio"], "periodo_inicio": granulo["inicio"], "periodo_fim": granulo["fim"],
        "variante": variante, "valor": f"{v:.6f}" if situacao == "ok" else "",
        "qualidade": "" if extraido["qualidade"] is None else str(extraido["qualidade"]),
        "situacao": situacao,
        "linha_arquivo": "" if extraido["linha_arquivo"] is None else str(extraido["linha_arquivo"]),
        "coluna_arquivo": "" if extraido["coluna_arquivo"] is None else str(extraido["coluna_arquivo"]),
        "granulo": granulo["titulo"], "obtido_em": obtido_em,
    }


# ---------------------------------------------------------------- rede


def _token() -> str:
    tok = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if not tok:
        raise FonteIndisponivel("EARTHDATA_TOKEN não definido no ambiente; os arquivos SMAP não podem ser baixados.")
    return tok


def buscar_granulos(ficha: dict, inicio: dt.date, fim: dt.date, cliente: httpx.Client | None = None) -> list[dict]:
    """Grânulos da coleção no período (CMR público). Cada um: título, início, fim e URL do .h5."""
    params = {"collection_concept_id": ficha["concept_id"], "page_size": 2000, "sort_key": "start_date",
              "temporal": f"{inicio.isoformat()}T00:00:00Z,{fim.isoformat()}T23:59:59Z"}
    c = cliente or httpx.Client(timeout=60)
    try:
        r = c.get(CMR_GRANULOS, params=params)
    except httpx.HTTPError as e:
        raise FonteIndisponivel(f"CMR da NASA não respondeu: {type(e).__name__}") from e
    if r.status_code != 200:
        raise FonteIndisponivel(f"CMR da NASA respondeu HTTP {r.status_code}")
    por_inicio: dict[str, dict] = {}
    for e in r.json().get("feed", {}).get("entry", []):
        h5 = [l["href"] for l in e.get("links", []) if l.get("href", "").endswith(".h5") and l["href"].startswith("https")]
        if not h5:
            continue
        g = {"titulo": h5[0].rsplit("/", 1)[-1], "inicio": e["time_start"], "fim": e.get("time_end") or e["time_start"],
             "url": h5[0], "atualizado_cmr": e.get("updated")}
        # Reprocessamento: o mesmo dia pode ter _001 e _002; fica o maior contador (mais recente).
        atual = por_inicio.get(g["inicio"])
        if atual is None or g["titulo"] > atual["titulo"]:
            por_inicio[g["inicio"]] = g
    return [por_inicio[k] for k in sorted(por_inicio)]


def url_opendap(ficha: dict, granulo: dict) -> str:
    return f"{OPENDAP}/collections/{ficha['concept_id']}/granules/{granulo['titulo']}.dap.nc4"


def restricao_dap4(ficha: dict, linha: int, coluna: int) -> str:
    """Expressão DAP4 que pede só a célula (valor, qualidade e índices de cada variante)."""
    sel = f"[{linha}:1:{linha}][{coluna}:1:{coluna}]"
    caminhos = [c for v in ficha["variaveis"].values() for c in v.values() if c]
    return ";".join(f"/{c}{sel}" for c in caminhos)


def baixar_recorte(ficha: dict, granulo: dict, linha: int, coluna: int, cliente: httpx.Client | None = None) -> bytes:
    c = cliente or httpx.Client(timeout=120, follow_redirects=True)
    try:
        r = c.get(url_opendap(ficha, granulo), params={"dap4.ce": restricao_dap4(ficha, linha, coluna)},
                  headers={"Authorization": f"Bearer {_token()}"})
    except httpx.HTTPError as e:
        raise FonteIndisponivel(f"OPeNDAP da NASA não respondeu: {type(e).__name__}") from e
    if r.status_code != 200 or r.content[:4] != b"\x89HDF":
        raise FonteIndisponivel(f"OPeNDAP da NASA respondeu HTTP {r.status_code} sem arquivo HDF5")
    return r.content


def baixar_granulo(url: str, cliente: httpx.Client | None = None) -> bytes:
    c = cliente or httpx.Client(timeout=300, follow_redirects=True)
    try:
        r = c.get(url, headers={"Authorization": f"Bearer {_token()}"})
    except httpx.HTTPError as e:
        raise FonteIndisponivel(f"NSIDC não respondeu: {type(e).__name__}") from e
    if r.status_code != 200 or r.content[:4] != b"\x89HDF":
        raise FonteIndisponivel(f"NSIDC respondeu HTTP {r.status_code} sem arquivo HDF5")
    return r.content


def atualizar_celula(dir_cache: Path, produto: str, ficha: dict, grade: str, linha: int, coluna: int,
                     inicio: dt.date, fim: dt.date, cliente: httpx.Client | None = None, recorte: bool = True) -> Path:
    """Baixa o período da NSIDC e grava no cache. Lança FonteIndisponivel se a fonte cair."""
    hoje = dt.date.today().isoformat()
    registros, unidade = [], None
    for g in buscar_granulos(ficha, inicio, fim, cliente):
        conteudo = baixar_recorte(ficha, g, linha, coluna, cliente) if recorte else baixar_granulo(g["url"], cliente)
        with h5py.File(io.BytesIO(conteudo), "r") as h5:
            for variante in ficha["variaveis"]:
                ex = extrair_celula(h5, ficha, variante, linha, coluna, recorte=recorte)
                unidade = unidade or ex["unidade_no_arquivo"]
                registros.append(registro(ficha, variante, g, ex, hoje))
    # A versão vem da coleção CMR consultada: grânulos de um concept_id pertencem a uma só versão.
    meta = {"produto": produto, "versao": ficha["versao"], "versao_fonte": f"coleção CMR {ficha['concept_id']}", "unidade_no_arquivo": unidade, "url": OPENDAP if recorte else CMR_GRANULOS,
            "concept_id": ficha["concept_id"], "obtido_em": hoje, "sintetico": False}
    return gravar_cache(dir_cache, produto, grade, linha, coluna, registros, meta)

