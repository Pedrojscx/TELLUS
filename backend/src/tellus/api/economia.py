"""Rotas da spec 007 (economia)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from tellus.economia import servico
from tellus.motor import servico as motor

router = APIRouter(prefix="/api/economia")


class PedidoMargem(BaseModel):
    lat: float
    lon: float
    cultura: Literal["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"]
    perda_relativa_quantis: dict[str, float] | None = None
    simulacao: dict | None = None  # pedido do motor (006); se vier, a perda é simulada aqui
    edicoes: dict[str, float | str] | None = None
    percentis: dict[str, int | str] | None = None


@router.post("/margem")
def margem(p: PedidoMargem) -> dict:
    perdas = p.perda_relativa_quantis
    versao_motor = None
    if p.simulacao is not None:
        sim = motor.simular(p.simulacao | {"lat": p.lat, "lon": p.lon, "cultura": p.cultura})
        perdas = sim["resultado"]["perda_relativa_quantis"]
        versao_motor = sim["versao_entradas"]
    r = servico.margem(p.lat, p.lon, p.cultura, perdas, p.edicoes, p.percentis)
    return r | {"versao_entradas_motor": versao_motor}


@router.get("/praca")
def praca(lat: float, lon: float, cultura: str) -> dict:
    pr = servico.praca_mais_proxima(lat, lon, cultura)
    if pr is None:
        return {"cultura": cultura, "disponivel": False, "motivo": "Sem planilha de custo da Conab para esta cultura."}
    return {"cultura": cultura, "disponivel": True, "praca": f"{pr['praca']}-{pr['uf']}", "distancia_km": pr["distancia_km"],
            "planilha": pr["aba"], "mes_referencia": pr["mes_referencia"], "sistema": pr["sistema"]}
