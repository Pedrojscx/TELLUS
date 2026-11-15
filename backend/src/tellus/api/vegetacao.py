"""Rotas da spec 009 — vegetação MODIS e HLS como contexto histórico.

Os erros viram JSON aqui mesmo (sem handler global), no mesmo formato do restante da API:
{"erro": {"codigo", "mensagem", "origem", "campo"}}.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from tellus.localizacao.servico import ErroLocalizacao
from tellus.vegetacao import servico
from tellus.vegetacao.servico import ErroVegetacao

router = APIRouter(prefix="/api/vegetacao")


def _executar(**kw) -> dict | JSONResponse:
    try:
        return servico.contexto(**kw)
    except ErroVegetacao as e:
        return JSONResponse(
            status_code=e.status,
            content={"erro": {"codigo": e.codigo, "mensagem": e.mensagem, "origem": e.origem, "campo": e.campo}},
        )
    except ErroLocalizacao as e:
        return JSONResponse(
            status_code=e.status,
            content={"erro": {"codigo": e.codigo, "mensagem": e.mensagem, "origem": "pedido", "campo": e.campo}},
        )


@router.get("/contexto")
def contexto_ponto(
    lat: str = Query(...),
    lon: str = Query(...),
    indice: Literal["ndvi", "evi"] | None = None,
    inicio: str | None = None,
    fim: str | None = None,
):
    return _executar(lat=lat, lon=lon, indice=indice, inicio=inicio, fim=fim)


@router.post("/contexto")
def contexto_geometria(
    geometria: dict = Body(...),
    id_geometria: str = Body(...),
    indice: Literal["ndvi", "evi"] | None = Body(None),
    inicio: str | None = Body(None),
    fim: str | None = Body(None),
):
    return _executar(geometria=geometria, id_geometria=id_geometria, indice=indice, inicio=inicio, fim=fim)
