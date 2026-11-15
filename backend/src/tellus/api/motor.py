"""Rotas da spec 006 (motor hídrico)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from tellus.motor import servico

router = APIRouter(prefix="/api/motor")


class Solo(BaseModel):
    textura: str | None = None
    granulometria: dict[str, float] | None = None
    classe: str | None = None
    cad_mm: float | None = None


class Entressafra(BaseModel):
    manejo: Literal["pousio", "palhada"] = "palhada"
    kc: float | None = None


class PedidoSimulacao(BaseModel):
    lat: float
    lon: float
    codigo_ibge: str | None = None
    cultura: Literal["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"]
    grupo: str | None = "GRUPO I"
    solo: Solo
    data_colheita_soja: str
    data_plantio: str | None = None
    entressafra: Entressafra | None = None
    armazenamento_inicial_frac: float | None = None
    edicoes: dict[str, float | list[float]] | None = None


def _dict(p: PedidoSimulacao) -> dict:
    d = p.model_dump(exclude_none=True)
    return d


@router.post("/simular")
def simular(p: PedidoSimulacao) -> dict:
    return servico.simular(_dict(p))


@router.post("/janela")
def janela(p: PedidoSimulacao) -> dict:
    return servico.simular_janela(_dict(p))
