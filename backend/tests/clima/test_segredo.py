"""Princípio VIII: o token Earthdata não aparece em cache, referências nem respostas."""

import os
from pathlib import Path

from fastapi.testclient import TestClient

from tellus.api.app import app

RAIZ = Path(__file__).resolve().parents[3]


def _token_real() -> str | None:
    if os.environ.get("EARTHDATA_TOKEN"):
        return os.environ["EARTHDATA_TOKEN"]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("EARTHDATA_TOKEN="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def test_token_fora_dos_arquivos_e_respostas():
    tok = _token_real()
    if not tok:
        return
    alvos = [RAIZ / "data" / "raw" / "clima", RAIZ / "referencias", RAIZ / "data" / "processed"]
    for base in alvos:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.stat().st_size < 50_000_000:
                assert tok not in p.read_bytes().decode("utf-8", "ignore"), f"token encontrado em {p}"
    corpo = TestClient(app).get("/api/clima/resumo", params={"lat": -17.785, "lon": -50.965}).text
    assert tok not in corpo
