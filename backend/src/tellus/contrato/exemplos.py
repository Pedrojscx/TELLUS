"""Gera os esquemas e os exemplos gravados do contrato (SC-001, SC-002).

Uso: cd backend && uv run python -m tellus.contrato.exemplos ../specs/011-contrato-api/contracts

A resposta de exemplo usa os módulos REAIS 006 e 007 com a série versionada de Rio Verde/GO (offline).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import regras, secoes, versao
from .modelos import PedidoCalculo, RespostaCalculo

LAT, LON = -17.785278, -50.965  # Rio Verde-GO, caso de referência

PEDIDO_VALIDO = {
    "versao_contrato": versao.VERSAO,
    "area": {"tipo": "ponto", "lat": LAT, "lon": LON, "confirmada": True},
    "data_colheita_soja": "2027-01-20",
    "solo": {"textura": "argilosa"},
    "grupo": "GRUPO I",
    "metodologia": "comparar_alternativas",
    "premissas_editadas": [
        {"modulo": "economia", "id": "preco_r_saca", "valor_novo": 55.0, "unidade": "R$/saca de 60 kg",
         "cultura": "sorgo_granifero_2a_safra", "origem_informada": "cotação de exemplo (cooperativa fictícia)",
         "data_informada": "2026-11-14"},
    ],
    "contextos": {"vegetacao": False, "umidade": False},
}

_QUADRADO_CRUZADO = [[-50.97, -17.79], [-50.96, -17.78], [-50.97, -17.78], [-50.96, -17.79], [-50.97, -17.79]]

EXEMPLOS_ERRO = {
    "pedido_versao_incompativel.json": (PEDIDO_VALIDO | {"versao_contrato": "2.0.0"}, "versao_incompativel"),
    "pedido_versao_ausente.json": ({k: v for k, v in PEDIDO_VALIDO.items() if k != "versao_contrato"}, "versao_ausente"),
    "pedido_geometria_invalida.json": (PEDIDO_VALIDO | {"area": {"tipo": "geometria", "id_geometria": "exemplo-cruzado",
                                                                 "origem": "desenho", "confirmada": True,
                                                                 "geometria": {"type": "Polygon", "coordinates": [_QUADRADO_CRUZADO]}}},
                                       "geometria_invalida"),
    "pedido_area_nao_confirmada.json": (PEDIDO_VALIDO | {"area": PEDIDO_VALIDO["area"] | {"confirmada": False}}, "pedido_invalido"),
    "pedido_sem_solo.json": ({k: v for k, v in PEDIDO_VALIDO.items() if k != "solo"}, "pedido_invalido"),
}


def resposta_exemplo() -> dict:
    return secoes.calcular(regras.normalizar_pedido(PEDIDO_VALIDO))


def _gravar(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def gerar(destino: Path) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    ex = destino / "exemplos"
    ex.mkdir(exist_ok=True)
    feitos = [destino / "pedido.schema.json", destino / "resposta.schema.json", ex / "pedido_valido.json", ex / "resposta_rio_verde.json"]
    _gravar(feitos[0], PedidoCalculo.model_json_schema())
    _gravar(feitos[1], RespostaCalculo.model_json_schema())
    _gravar(feitos[2], PEDIDO_VALIDO)
    _gravar(feitos[3], resposta_exemplo())
    for nome, (pedido, codigo) in EXEMPLOS_ERRO.items():
        _gravar(ex / nome, {"pedido": pedido, "erro_esperado": codigo})
        feitos.append(ex / nome)
    return feitos


if __name__ == "__main__":
    for p in gerar(Path(sys.argv[1] if len(sys.argv) > 1 else "../specs/011-contrato-api/contracts")):
        print(p)
