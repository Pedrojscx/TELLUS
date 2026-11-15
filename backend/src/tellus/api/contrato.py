"""Rotas da spec 011 (contrato): versão, esquema, validação e cálculo completo (006, 007, 008 e contextos 009/010).

Erros no envelope unificado proposto: {"erro": {codigo, mensagem, origem, campo, versoes_aceitas?, detalhes?}}.
Basta `app.include_router(contrato.router)`: o router trata os próprios erros.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from tellus import i18n
from tellus.contrato import regras, secoes, versao
from tellus.contrato.modelos import PedidoCalculo, RespostaCalculo

router = APIRouter(prefix="/api/contrato")


def _idioma(pedido: Any, request: Request) -> str:
    """Campo `idioma` do pedido (1.2.0) ou, sem ele, o cabeçalho Accept-Language (spec 014, FR-005)."""
    campo = pedido.get("idioma") if isinstance(pedido, dict) else None
    return i18n.normalizar_idioma(campo or request.headers.get("accept-language"))


def _erro(e: versao.ErroContrato, idioma: str = i18n.PADRAO) -> JSONResponse:
    return JSONResponse(status_code=e.status, content={"erro": i18n.traduzir_resposta(e.como_dict(), idioma)},
                        headers={"Content-Language": idioma})


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
def calcular(request: Request, pedido: Any = Body(...)):
    """Pedido do contrato → resposta rastreável (#54). Erros no envelope único; seções com erro não derrubam a resposta.
    Em inglês (spec 014), só os campos de texto mudam; números, códigos e ordem são os mesmos."""
    idioma = _idioma(pedido, request)
    try:
        p = regras.normalizar_pedido(pedido)
        ctx = {m: _contexto_real(m, p) for m in ("vegetacao", "umidade")}
        resp = secoes.calcular(p, ctx)
    except versao.ErroContrato as e:
        return _erro(e, idioma)
    corpo = i18n.traduzir_resposta(jsonable_encoder(resp), idioma)
    corpo["idioma"] = idioma
    return JSONResponse(content=corpo, headers={"Content-Language": idioma})


@router.post("/pedido/validar")
def validar(request: Request, pedido: Any = Body(...)):
    try:
        return {"valido": True, "versao_contrato": versao.VERSAO, "pedido": regras.normalizar_pedido(pedido)}
    except versao.ErroContrato as e:
        return _erro(e, _idioma(pedido, request))
