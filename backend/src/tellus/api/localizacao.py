"""Rotas da spec 001 (contracts/localizacao.openapi.yaml)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from tellus.localizacao import busca, servico
from tellus.localizacao.referencias import carregar

router = APIRouter(prefix="/api")


@router.get("/municipios")
def buscar_municipios(
    busca_: str = Query(..., alias="busca", min_length=2),
    limite: int = Query(busca.LIMITE_PADRAO, ge=1, le=busca.LIMITE_MAXIMO),
) -> dict:
    return {"resultados": busca.buscar(carregar().municipios_ordenados, busca_, limite)}


@router.get("/localizacao/padrao")
def localizacao_padrao() -> dict:
    return servico.resolver_padrao(carregar())


@router.get("/localizacao/municipio/{codigo_ibge}")
def localizacao_municipio(codigo_ibge: str) -> dict:
    return servico.resolver_municipio(carregar(), codigo_ibge)


@router.get("/localizacao")
def localizacao(
    lat: str = Query(...),
    lon: str = Query(...),
    meio: Literal["coordenadas", "mapa"] = "coordenadas",
) -> dict:
    # lat/lon como texto: a validação (e a mensagem) é do domínio, não do FastAPI.
    return servico.resolver(carregar(), lat, lon, meio=meio)
