"""App FastAPI do TELLUS."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tellus.api import car, clima, contrato, culturas, economia, localizacao, motor, recomendacao, umidade, vegetacao, zarc
from tellus.car.servico import ErroCar
from tellus.zarc.servico import ErroZarc
from tellus.culturas.servico import ErroPremissa
from tellus.motor.servico import ErroMotor
from tellus.economia.servico import ErroEconomia
from tellus.recomendacao.servico import ErroRecomendacao
from tellus.clima.servico import ErroClima
from tellus.localizacao.servico import ErroLocalizacao

app = FastAPI(title="TELLUS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://127.0.0.1:4321"],
    # D-010: celular na mesma rede Wi-Fi abre o site pelo IP do computador (só rede local, sem deploy)
    allow_origin_regex=r"http://(192\.168|10|172\.(1[6-9]|2\d|3[01]))(\.\d{1,3}){2,3}:4321",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _erro(status: int, codigo: str, mensagem: str, campo: str | None = None, origem: str | None = None) -> JSONResponse:
    """Envelope único de erro (spec 011): {"erro": {codigo, mensagem, origem, campo}}."""
    return JSONResponse(status_code=status,
                        content={"erro": {"codigo": codigo, "mensagem": mensagem, "origem": origem, "campo": campo}})


@app.exception_handler(ErroLocalizacao)
async def _erro_localizacao(_: Request, exc: ErroLocalizacao) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "pedido")


@app.exception_handler(RequestValidationError)
async def _erro_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    primeiro = exc.errors()[0] if exc.errors() else {}
    campo = str(primeiro.get("loc", ["", ""])[-1]) or None
    return _erro(422, "parametro_invalido", primeiro.get("msg", "Parâmetro inválido."), campo, "pedido")


@app.exception_handler(ErroClima)
async def _erro_clima(_: Request, exc: ErroClima) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, getattr(exc, "campo", None), exc.origem)


@app.exception_handler(ErroCar)
async def _erro_car(_: Request, exc: ErroCar) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "SICAR" if exc.status >= 500 else "pedido")


@app.exception_handler(ErroZarc)
async def _erro_zarc(_: Request, exc: ErroZarc) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "ZARC/MAPA (SISZARC)")


@app.exception_handler(ErroPremissa)
async def _erro_premissa(_: Request, exc: ErroPremissa) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "spec 005")


@app.exception_handler(ErroMotor)
async def _erro_motor(_: Request, exc: ErroMotor) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "spec 006")


@app.exception_handler(ErroEconomia)
async def _erro_economia(_: Request, exc: ErroEconomia) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "spec 007")


@app.exception_handler(ErroRecomendacao)
async def _erro_recomendacao(_: Request, exc: ErroRecomendacao) -> JSONResponse:
    return _erro(exc.status, exc.codigo, exc.mensagem, exc.campo, "spec 008")


app.include_router(localizacao.router)
app.include_router(recomendacao.router)
app.include_router(economia.router)
app.include_router(motor.router)
app.include_router(culturas.router)
app.include_router(zarc.router)
app.include_router(car.router)
app.include_router(clima.router)
app.include_router(umidade.router)
app.include_router(vegetacao.router)
app.include_router(contrato.router)


@app.get("/api/saude")
def saude() -> dict:
    return {"status": "ok"}


# Contextos opcionais da rota /api/contrato/calcular (009/010): plugados aqui para o contrato não importá-los.
from tellus.umidade import servico as _umidade_servico  # noqa: E402
from tellus.vegetacao import servico as _vegetacao_servico  # noqa: E402

contrato.PROVEDORES_CONTEXTO.update({"vegetacao": _vegetacao_servico.contexto, "umidade": _umidade_servico.contexto})
