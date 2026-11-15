"""Rotas da spec 001 (CAR) e da confirmação de lavoura."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Body, File, UploadFile
from pydantic import BaseModel

from tellus.car import servico
from tellus.lavoura import servico as lavoura

router = APIRouter(prefix="/api")

# Limite de arquivo (D-009), lido do arquivo único de limites; mesmo valor que o upload já aplicava (20 MB).
MAX_UPLOAD = int(servico.LIMITES_UNICOS["arquivo_max_bytes"]["valor"])


@router.get("/car/{codigo}")
def consultar_car(codigo: str) -> dict:
    return servico.consultar(codigo)


@router.post("/car/upload")
async def upload_sicar(arquivo: UploadFile = File(...)) -> dict:
    conteudo = await arquivo.read()
    if len(conteudo) > MAX_UPLOAD:
        raise servico.ErroCar("arquivo_grande", "O arquivo passa de 20 MB.", "arquivo", status=413)
    return servico.upload_sicar(conteudo, arquivo.filename or "")


@router.post("/lavoura/arquivo")
async def lavoura_arquivo(arquivo: UploadFile = File(...)) -> dict:
    """Spec 002: KML, KMZ, GeoJSON ou Shapefile .zip; uma lavoura por envio; mesmo resumo e mesma confirmação."""
    conteudo = await arquivo.read()
    if len(conteudo) > MAX_UPLOAD:
        raise servico.ErroCar("arquivo_grande", f"O arquivo passa do limite de {MAX_UPLOAD // (1024 * 1024)} MB.", "arquivo", status=413)
    return lavoura.de_arquivo(conteudo, arquivo.filename or "")


@router.post("/lavoura/desenho")
def lavoura_desenho(geometria: dict = Body(..., embed=True)) -> dict:
    """Spec 002: polígono desenhado no mapa → mesma validação, mesmo resumo territorial, mesma confirmação."""
    return lavoura.de_desenho(geometria)


@router.get("/lavoura/limites")
def lavoura_limites() -> dict:
    lim = lavoura.limites()
    return {k: lim[k] for k in ("arquivo_max_bytes", "arquivo_formatos", "lavouras_por_envio", "vertices_total_max", "area_max_ha")}


class PedidoConfirmacao(BaseModel):
    geometria: dict
    id_geometria: str
    origem: Literal["car", "upload_sicar", "desenho", "arquivo"]
    proveniencia: dict | None = None


@router.post("/lavoura/confirmar")
def confirmar(p: PedidoConfirmacao) -> dict:
    return servico.confirmar(p.geometria, p.id_geometria, p.origem, p.proveniencia)
