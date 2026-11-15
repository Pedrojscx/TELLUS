"""Prepara o cache de umidade SMAP de uma célula (spec 010).

Uso (na raiz do repositório):
    uv run --project backend python scripts/preparar_umidade.py --lat -17.785 --lon -50.965 --dias 30
    uv run --project backend python scripts/preparar_umidade.py ... --exportar-referencia rio_verde_go

Passos:
1. Lista os grânulos no CMR, que é público e não pede login, e grava o bruto em
   data/raw/umidade/cmr/<produto>_<inicio>_<fim>.json com um .meta.json. Assim ficam registradas
   a latência e os reprocessamentos.
2. Com EARTHDATA_TOKEN no ambiente, baixa por OPeNDAP DAP4 só a célula de cada dia e grava em
   data/raw/umidade/<produto>/ (fora do Git). Sem token, para e diz o motivo, sem inventar dado.
3. `--exportar-referencia NOME` copia a série derivada da célula para referencias/umidade/NOME/,
   com meta e sha256, para a demonstração rodar sem rede.

Produto e janela padrão são a HIPÓTESE OPERACIONAL do protótipo (#70), não uma decisão aprovada.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend" / "src"))

from tellus.umidade import cliente, regras, servico  # noqa: E402

DIR_RAW = RAIZ / "data" / "raw" / "umidade"


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--produto", default=servico.PRODUTO_HIPOTESE)
    ap.add_argument("--dias", type=int, default=servico.JANELA_DIAS)
    ap.add_argument("--fim", default=dt.date.today().isoformat(), help="último dia (AAAA-MM-DD), padrão hoje")
    ap.add_argument("--exportar-referencia", metavar="NOME")
    a = ap.parse_args()

    fi = servico.ficha()
    f = fi["produtos"][a.produto]
    grade = fi["grades"][f["grade"]]
    lc = regras.celula_ease2(a.lat, a.lon, grade["colunas"], grade["linhas"])
    if lc is None:
        print("Ponto fora da grade EASE-Grid 2.0.")
        return 2
    lin, col = lc
    cel = regras.descrever_celula(a.lat, a.lon, f["grade"], grade)
    fim = dt.date.fromisoformat(a.fim)
    inicio = fim - dt.timedelta(days=a.dias - 1)
    print(f"{a.produto} V{f['versao']}: célula {f['grade']} linha {lin} coluna {col}, centro "
          f"({cel['centro_lat']}, {cel['centro_lon']}), {cel['distancia_km']} km do ponto; período {inicio}..{fim}")

    # 1. CMR (público)
    with httpx.Client(timeout=60) as c:
        granulos = cliente.buscar_granulos(f, inicio, fim, c)
        r = c.get(cliente.CMR_GRANULOS, params={"collection_concept_id": f["concept_id"], "page_size": 2000,
                                                 "sort_key": "start_date",
                                                 "temporal": f"{inicio}T00:00:00Z,{fim}T23:59:59Z"})
    bruto = DIR_RAW / "cmr" / f"{a.produto}_{inicio}_{fim}.json"
    bruto.parent.mkdir(parents=True, exist_ok=True)
    bruto.write_bytes(r.content)
    hoje = dt.date.today().isoformat()
    latencias = []
    for g in granulos:
        if g.get("atualizado_cmr"):
            dia_fim = dt.datetime.fromisoformat(g["fim"].replace("Z", "+00:00"))
            pub = dt.datetime.fromisoformat(g["atualizado_cmr"].replace("Z", "+00:00"))
            latencias.append(round((pub - dia_fim).total_seconds() / 3600, 1))
    meta_cmr = {"url": str(r.request.url), "obtido_em": hoje, "http": r.status_code, "sha256": _sha256(bruto),
                "granulos_unicos": len(granulos), "entradas_cmr": len(r.json().get("feed", {}).get("entry", [])),
                "dias_sem_granulo": sorted({(inicio + dt.timedelta(days=i)).isoformat() for i in range(a.dias)}
                                           - {g["inicio"][:10] for g in granulos}),
                "latencia_horas_fim_do_dia_ate_ultima_atualizacao_cmr": {
                    "min": min(latencias, default=None), "max": max(latencias, default=None),
                    "nota": "'updated' do CMR conta a última atualização; reprocessamentos (_002) aumentam o valor"},
                "sintetico": False}
    bruto.with_suffix(".json.meta.json").write_text(json.dumps(meta_cmr, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"CMR: {len(granulos)} grânulos únicos; dias sem grânulo: {meta_cmr['dias_sem_granulo']}; bruto em {bruto}")

    # 2. Recorte por OPeNDAP (precisa de login)
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        print("BLOQUEIO: EARTHDATA_TOKEN não está no ambiente. A NSIDC e o OPeNDAP respondem HTTP 302 para "
              "urs.earthdata.nasa.gov sem login. Nenhum valor foi baixado ou inventado.")
        return 3
    try:
        p = cliente.atualizar_celula(DIR_RAW, a.produto, f, f["grade"], lin, col, inicio, fim)
    except cliente.FonteIndisponivel as e:
        print(f"BLOQUEIO: {e}")
        return 4
    print(f"cache: {p}")
    r = servico.contexto(a.lat, a.lon, produto=a.produto, dir_cache=DIR_RAW, janela_dias=a.dias)
    print("contagem na janela:", json.dumps(r["regra_periodo"]["contagem"], ensure_ascii=False))
    for i in r["itens"]:
        print(" ", i["periodo"].get("data"), i["periodo"].get("variante"), i["valor"], i["qualidade"].get("flag"))

    # 3. Série derivada versionada (opcional)
    if a.exportar_referencia:
        destino = RAIZ / "referencias" / "umidade" / a.exportar_referencia
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy(p, destino / "serie.csv")
        meta = json.loads(cliente.arquivo_meta(DIR_RAW, a.produto).read_text(encoding="utf-8"))
        meta |= {"celula": cel, "periodo": {"inicio": str(inicio), "fim": str(fim)}, "sha256_serie": _sha256(destino / "serie.csv")}
        (destino / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        print(f"referência versionada em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
