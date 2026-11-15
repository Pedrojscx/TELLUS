"""Rotas da spec 011 (contrato). Só validam e descrevem o contrato: nenhuma executa 006, 007 ou 008.

Erros no envelope unificado proposto: {"erro": {codigo, mensagem, origem, campo, versoes_aceitas?, detalhes?}}.
Basta `app.include_router(contrato.router)`: o router trata os próprios erros.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from tellus.contrato import regras, versao
from tellus.contrato.modelos import PedidoCalculo, RespostaCalculo

router = APIRouter(prefix="/api/contrato")


def _erro(e: versao.ErroContrato) -> JSONResponse:
    return JSONResponse(status_code=e.status, content={"erro": e.como_dict()})


@router.get("/versao")
def ver_versao() -> dict:
    return {
        "versao_contrato": versao.VERSAO, "versoes_aceitas": versao.versoes_aceitas(), "regra_compatibilidade": versao.REGRA,
        "limites": regras.limites(),
        "secoes": {"risco_hidrico": "disponivel (spec 006)", "economia": "disponivel (spec 007)",
                   "recomendacao": "pendente (spec 008, #48)"},
        "contextos_opcionais": ["vegetacao (spec 009)", "umidade (spec 010)"],
    }


@router.get("/esquema")
def esquema() -> dict:
    return {"versao_contrato": versao.VERSAO, "pedido": PedidoCalculo.model_json_schema(),
            "resposta": RespostaCalculo.model_json_schema()}


@router.post("/pedido/validar")
def validar(pedido: Any = Body(...)):
    try:
        return {"valido": True, "versao_contrato": versao.VERSAO, "pedido": regras.normalizar_pedido(pedido)}
    except versao.ErroContrato as e:
        return _erro(e)
