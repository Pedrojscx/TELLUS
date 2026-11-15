"""Rotas da spec 001 (CAR) e da confirmação de lavoura."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from tellus.car import servico

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


class PedidoConfirmacao(BaseModel):
    geometria: dict
    id_geometria: str
    origem: Literal["car", "upload_sicar", "desenho", "arquivo"]
    proveniencia: dict | None = None


@router.post("/lavoura/confirmar")
def confirmar(p: PedidoConfirmacao) -> dict:
    return servico.confirmar(p.geometria, p.id_geometria, p.origem, p.proveniencia)
