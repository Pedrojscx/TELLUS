"""Rotas da spec 010: umidade SMAP como contexto regional opcional.

O router trata os próprios erros (ErroUmidade e ErroLocalizacao) e devolve
`{"erro": {"codigo", "mensagem", "origem"}}`. Basta `app.include_router(umidade.router)`.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from tellus.localizacao.servico import ErroLocalizacao
from tellus.umidade import servico
from tellus.umidade.servico import ErroUmidade

router = APIRouter(prefix="/api/umidade")


def _erro(status: int, codigo: str, mensagem: str, origem: str | None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": {"codigo": codigo, "mensagem": mensagem, "origem": origem}})


def _executar(**kw):
    try:
        return servico.contexto(**kw)
    except ErroUmidade as e:
        return _erro(e.status, e.codigo, e.mensagem, e.origem)
    except ErroLocalizacao as e:
        return _erro(e.status, e.codigo, e.mensagem, e.campo)


@router.get("/produtos")
def produtos() -> dict:
    return servico.produtos()


@router.get("/contexto")
def contexto(lat: str = Query(...), lon: str = Query(...), produto: str | None = None, variante: str | None = None,
             data: str | None = None, inicio: str | None = None, fim: str | None = None):
    return _executar(lat=lat, lon=lon, produto=produto, variante=variante, data=data, inicio=inicio, fim=fim)


@router.post("/contexto")
def contexto_geometria(geometria: dict = Body(..., embed=True), produto: str | None = Body(None, embed=True),
                       variante: str | None = Body(None, embed=True), data: str | None = Body(None, embed=True),
                       inicio: str | None = Body(None, embed=True), fim: str | None = Body(None, embed=True)):
    if geometria.get("type") not in ("Point", "Polygon", "MultiPolygon"):
        return _erro(422, "geometria_invalida", "Envie um GeoJSON Point, Polygon ou MultiPolygon em 'geometria'.", "pedido")
    return _executar(geometria=geometria, produto=produto, variante=variante, data=data, inicio=inicio, fim=fim)
