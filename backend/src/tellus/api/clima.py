"""Rotas da spec 003 (contracts/clima.openapi.yaml)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Body, Query

from tellus.clima import servico

router = APIRouter(prefix="/api/clima")


@router.get("/resumo")
def resumo(lat: str = Query(...), lon: str = Query(...)) -> dict:
    return servico.resumo(lat, lon)


@router.get("/serie")
def serie(lat: str = Query(...), lon: str = Query(...), inicio: str | None = None, fim: str | None = None) -> dict:
    return servico.serie(lat, lon, inicio, fim)


@router.post("/serie")
def serie_area(
    geometria: dict = Body(...),
    id_geometria: str = Body(...),
    inicio: str | None = Body(None),
    fim: str | None = Body(None),
) -> dict:
    """Área confirmada (spec 002/CAR): chuva média ponderada pelas células IMERG de 0,1° que ela cruza."""
    return servico.serie(geometria=geometria, id_geometria=id_geometria, inicio=inicio, fim=fim)


@router.post("/resumo")
def resumo_area(geometria: dict = Body(...), id_geometria: str = Body(...)) -> dict:
    return servico.resumo(geometria=geometria, id_geometria=id_geometria)


@router.get("/validacao")
def validacao(lat: str = Query(...), lon: str = Query(...), recorte: Literal["jan-jun", "todos"] = "jan-jun") -> dict:
    return servico.validacao(lat, lon, recorte)
