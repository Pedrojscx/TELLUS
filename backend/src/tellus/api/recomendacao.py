"""Rota da spec 008 (recomendação)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from tellus.api.motor import Entressafra, Solo
from tellus.recomendacao import servico

router = APIRouter(prefix="/api")


class PedidoRecomendacao(BaseModel):
    metodologia: Literal["cultura_escolhida", "calculo_completo"]
    cultura: Literal["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"] | None = None
    grupo: str | None = None  # vazio = "não sei": testa todos os grupos do ZARC
    lat: float
    lon: float
    codigo_ibge: str | None = None
    geometria: dict | None = None  # área confirmada da lavoura (002); chuva ponderada por área (003)
    id_geometria: str | None = None
    solo: Solo
    data_colheita_soja: str
    entressafra: Entressafra | None = None
    armazenamento_inicial_frac: float | None = None
    edicoes_cultura: dict[str, dict[str, float | list[float]]] | None = None
    edicoes_economia: dict[str, dict[str, float | str]] | None = None
    percentis: dict[str, int | str] | None = None
    informacoes_economia: dict[str, dict[str, dict[str, str]]] | None = None  # {cultura: {chave: {origem_informada, data_informada}}}


@router.post("/recomendacao")
def recomendar(p: PedidoRecomendacao) -> dict:
    return servico.recomendar(p.model_dump(exclude_none=True))
