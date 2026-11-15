"""Rotas da spec 003 (contracts/clima.openapi.yaml)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from tellus.clima import servico

router = APIRouter(prefix="/api/clima")


@router.get("/resumo")
def resumo(lat: str = Query(...), lon: str = Query(...)) -> dict:
    return servico.resumo(lat, lon)


@router.get("/serie")
def serie(lat: str = Query(...), lon: str = Query(...), inicio: str | None = None, fim: str | None = None) -> dict:
    return servico.serie(lat, lon, inicio, fim)


@router.get("/validacao")
def validacao(lat: str = Query(...), lon: str = Query(...), recorte: Literal["jan-jun", "todos"] = "jan-jun") -> dict:
    return servico.validacao(lat, lon, recorte)
