"""Rotas da spec 004 (calendário ZARC)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from tellus.zarc import servico

router = APIRouter(prefix="/api/zarc")


@router.get("/culturas")
def culturas() -> dict:
    return servico.CULTURAS


@router.get("/calendario")
def calendario(
    codigo_ibge: str = Query(..., pattern=r"^\d{7}$"),
    cultura: str = Query(...),
    grupo: str | None = Query(None, description="ex.: GRUPO I; vazio = não sei (todos os grupos)"),
    solo: str | None = Query(None, description="ex.: AD4 ou 3 (sorgo); vazio = todos"),
) -> dict:
    return servico.calendario(codigo_ibge, cultura, grupo or None, solo or None)


@router.get("/consulta")
def consulta(
    codigo_ibge: str = Query(..., pattern=r"^\d{7}$"),
    cultura: str = Query(...),
    data: str = Query(..., description="data de semeadura AAAA-MM-DD"),
    grupo: str | None = None,
    solo: str | None = None,
) -> dict:
    return servico.consultar_data(codigo_ibge, cultura, data, grupo or None, solo or None)
