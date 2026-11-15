"""D-009: um único arquivo de limites; valores expostos com status hipotese; tempo_excedido."""

import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tellus.api import car as rota_car
from tellus.api import contrato as rota_contrato
from tellus.contrato import exemplos, regras, secoes, versao

RAIZ = Path(__file__).resolve().parents[3]
UNICO = RAIZ / "backend" / "src" / "tellus" / "contrato" / "limites.json"
CHAVES = ("arquivo_max_bytes", "arquivo_formatos", "lavouras_por_envio", "vertices_total_max", "vertices_por_anel_max",
          "area_max_ha", "processamento_prazo_s", "max_vertices_anel")
# Sem exceções: a vegetação (009) também lê vertices_por_anel_max do arquivo único desde a integração da 011.
EXCECOES: set = set()


def test_um_unico_arquivo_define_os_limites():
    achados = []
    for p in list((RAIZ / "referencias").rglob("*.json")) + list((RAIZ / "backend" / "src").rglob("*.json")):
        if p == UNICO:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(d, dict) and set(d) & set(CHAVES):
            achados.append(f"{p.relative_to(RAIZ)}: {sorted(set(d) & set(CHAVES))}")
    padrao = re.compile(r"\d+\s*\*\s*1024\s*\*\s*1024|\b(20971520|10485760)\b|MAX_VERTICES\s*=\s*\d|max_vertices[^=\n]*=\s*\d")
    for p in (RAIZ / "backend" / "src").rglob("*.py"):
        if p in EXCECOES:
            continue
        for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if padrao.search(linha):
                achados.append(f"{p.relative_to(RAIZ)}:{i}: {linha.strip()}")
    assert achados == []


def test_valores_e_status():
    lim = regras.limites()
    assert lim["arquivo_max_bytes"]["valor"] == 20 * 1024 * 1024 and lim["vertices_total_max"]["valor"] == 10000
    assert lim["area_max_ha"]["valor"] == 100000 and lim["processamento_prazo_s"]["valor"] == 60
    assert lim["arquivo_formatos"]["valor"] == ["kml", "kmz", "geojson", "shapefile_zip"] and lim["lavouras_por_envio"]["valor"] == 1
    for k in CHAVES[:-1]:
        if k == "vertices_por_anel_max":
            assert lim[k]["valor"] == 5000 and "spec 001" in lim[k]["origem"]
            continue
        assert lim[k]["status"] == "hipotese" and lim[k]["decisao"] == "D-009" and lim[k]["issue"] == "#71"
        assert lim[k]["data"] == "2026-11-15" and "revisável" in lim[k]["revisao"]
    assert "upload_car_shapefile_max_bytes" not in lim


def test_versao_expoe_limites_com_status_hipotese():
    app = FastAPI()
    app.include_router(rota_contrato.router)
    j = TestClient(app).get("/api/contrato/versao").json()["limites"]
    assert j["vertices_total_max"] == regras.limites()["vertices_total_max"]
    assert {j[k]["status"] for k in ("arquivo_max_bytes", "vertices_total_max", "area_max_ha", "processamento_prazo_s")} == {"hipotese"}


def test_upload_car_le_o_limite_unico_e_recusa_acima(monkeypatch):
    assert rota_car.MAX_UPLOAD == regras.limites()["arquivo_max_bytes"]["valor"]
    app = FastAPI()
    app.include_router(rota_car.router)

    @app.exception_handler(rota_car.servico.ErroCar)
    async def _h(_, e):  # o handler real fica no app.py
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=e.status, content={"erro": {"codigo": e.codigo}})

    monkeypatch.setattr(rota_car.servico, "upload_sicar", lambda c, n="": {"ok": len(c)})
    cli = TestClient(app)
    grande = cli.post("/api/car/upload", files={"arquivo": ("a.zip", b"0" * (rota_car.MAX_UPLOAD + 1))})
    assert grande.status_code == 413 and grande.json()["erro"]["codigo"] == "arquivo_grande"
    no_limite = cli.post("/api/car/upload", files={"arquivo": ("a.zip", b"0" * rota_car.MAX_UPLOAD)})
    assert no_limite.status_code == 200


def test_tempo_excedido_interrompe_sem_resultado_parcial():
    pedido = regras.normalizar_pedido(exemplos.PEDIDO_VALIDO | {"premissas_editadas": []})
    tempos = iter([0.0, 30.0, 61.0])  # início, depois do 1º motor, depois da 1ª margem
    with pytest.raises(versao.ErroContrato) as e:
        secoes.calcular(pedido, relogio=lambda: next(tempos))
    assert e.value.codigo == "tempo_excedido" and e.value.status == 504
    assert "Tente de novo" in e.value.mensagem and "cache" in e.value.mensagem and "D-009" in e.value.origem


def test_dentro_do_prazo_nao_interrompe():
    pedido = regras.normalizar_pedido(exemplos.PEDIDO_VALIDO | {"metodologia": "cultura_escolhida", "cultura": "milho_2a_safra",
                                                                "premissas_editadas": []})
    assert secoes.calcular(pedido, relogio=lambda: 0.0)["culturas"]
