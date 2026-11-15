"""App FastAPI do TELLUS."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tellus.api import localizacao
from tellus.localizacao.servico import ErroLocalizacao

app = FastAPI(title="TELLUS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _erro(status: int, codigo: str, mensagem: str, campo: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": {"codigo": codigo, "mensagem": mensagem, "campo": campo}})


@app.exception_handler(ErroLocalizacao)
async def _erro_localizacao(_: Request, exc: ErroLocalizacao) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo)


@app.exception_handler(RequestValidationError)
async def _erro_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    primeiro = exc.errors()[0] if exc.errors() else {}
    campo = str(primeiro.get("loc", ["", ""])[-1]) or None
    return _erro(422, "parametro_invalido", primeiro.get("msg", "Parâmetro inválido."), campo)


app.include_router(localizacao.router)


@app.get("/api/saude")
def saude() -> dict:
    return {"status": "ok"}
