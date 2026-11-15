"""Rotas da spec 005 (base de solo e culturas)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from tellus.culturas import servico

router = APIRouter(prefix="/api")


@router.get("/culturas")
def listar() -> dict:
    return {"culturas": servico.culturas(), "metodos_referencia": servico.BASE["metodos_referencia"]}


@router.get("/culturas/{cultura}/parametros")
def parametros(cultura: str, uf: str | None = None) -> dict:
    return servico.parametros(cultura, uf)


class PedidoPremissas(BaseModel):
    cultura: str
    uf: str | None = None
    edicoes: dict[str, float | list[float]] | None = None


@router.post("/culturas/premissas")
def premissas(p: PedidoPremissas) -> dict:
    return servico.premissas(p.cultura, p.uf, p.edicoes)


class PedidoSolo(BaseModel):
    cultura: str
    uf: str | None = None
    textura: str | None = None
    granulometria: dict[str, float] | None = None
    classe: str | None = None
    cad_mm: float | None = None


@router.post("/solo/classificar")
def classificar(p: PedidoSolo) -> dict:
    return servico.classificar_solo(p.cultura, p.uf, p.textura, p.granulometria, p.classe, p.cad_mm)
