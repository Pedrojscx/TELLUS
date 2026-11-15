"""Rotas da spec 011 (contrato): versão, esquema, validação e cálculo completo (006, 007, 008 e contextos 009/010).

Erros no envelope unificado proposto: {"erro": {codigo, mensagem, origem, campo, versoes_aceitas?, detalhes?}}.
Basta `app.include_router(contrato.router)`: o router trata os próprios erros.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from tellus.contrato import regras, secoes, versao
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
                   "recomendacao": "disponivel (spec 008)"},
        "contextos_opcionais": ["vegetacao (spec 009)", "umidade (spec 010)"],
    }


@router.get("/esquema")
def esquema() -> dict:
    return {"versao_contrato": versao.VERSAO, "pedido": PedidoCalculo.model_json_schema(),
            "resposta": RespostaCalculo.model_json_schema()}


# Provedores dos contextos opcionais (009/010), plugados pelo app.py. O contrato não importa os módulos de
# contexto: isolamento do SMAP (#53/#95) — eles nunca entram no cálculo principal.
PROVEDORES_CONTEXTO: dict[str, Any] = {}


def _contexto_real(modulo: str, pedido: dict) -> dict | None:
    """Chama o provedor da 009/010 só se o pedido pediu; erro do módulo vira {"erro": ...} (não afeta o principal)."""
    if not (pedido.get("contextos") or {}).get(modulo):
        return None
    provedor = PROVEDORES_CONTEXTO.get(modulo)
    if provedor is None:
        return None  # vira "contexto_nao_integrado" na resposta
    a = pedido["area"]
    kw = {"lat": a["lat"], "lon": a["lon"]} if a["tipo"] == "ponto" else {"geometria": a["geometria"], "id_geometria": a.get("id_geometria")}
    try:
        return provedor(**kw)
    except Exception as e:  # noqa: BLE001
        return {"erro": {"codigo": getattr(e, "codigo", type(e).__name__), "mensagem": getattr(e, "mensagem", str(e)),
                         "origem": getattr(e, "origem", None) or f"spec {modulo}", "campo": getattr(e, "campo", None)}}


@router.post("/calcular")
def calcular(pedido: Any = Body(...)):
    """Pedido do contrato → resposta rastreável (#54). Erros no envelope único; seções com erro não derrubam a resposta."""
    try:
        p = regras.normalizar_pedido(pedido)
        ctx = {m: _contexto_real(m, p) for m in ("vegetacao", "umidade")}
        return secoes.calcular(p, ctx)
    except versao.ErroContrato as e:
        return _erro(e)


@router.post("/pedido/validar")
def validar(pedido: Any = Body(...)):
    try:
        return {"valido": True, "versao_contrato": versao.VERSAO, "pedido": regras.normalizar_pedido(pedido)}
    except versao.ErroContrato as e:
        return _erro(e)
