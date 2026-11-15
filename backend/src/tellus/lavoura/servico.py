"""Desenho no mapa e arquivo (KML, KMZ, GeoJSON, Shapefile .zip) → candidato a lavoura (spec 002).

Mesmo caminho do CAR: validação (`car.regras.validar_poligono`, limite por anel), limites da D-009
(`contrato.regras.limites_excedidos`: vértices totais e área), resumo territorial (`car.servico.candidato`:
área em ha, todos os municípios atingidos, id_geometria) e a mesma confirmação (`/api/lavoura/confirmar`).
Nada é simplificado: acima dos limites, erro nomeado.
"""

from __future__ import annotations

import datetime as dt

from tellus.car import regras as car_regras
from tellus.car import servico as car
from tellus.contrato import regras as contrato

from . import arquivos

ORIGENS = ("desenho", "arquivo")


def limites() -> dict:
    return contrato.limites()


def validar(geom: dict, campo: str) -> None:
    """Geometria inválida ou acima dos limites → ErroCar nomeado (o handler do app devolve o envelope de erro)."""
    if not isinstance(geom, dict) or geom.get("type") not in ("Polygon", "MultiPolygon"):
        raise car.ErroCar("geometria_invalida", "Envie um polígono (Polygon ou MultiPolygon).", campo)
    erros = car_regras.validar_poligono(geom, car.MAX_VERTICES)
    if erros:
        raise car.ErroCar("geometria_invalida", "A geometria não é válida: " + "; ".join(erros), campo)
    excedidos = contrato.limites_excedidos(geom)
    if excedidos:
        raise car.ErroCar(excedidos[0][0], " ".join(m for _, m in excedidos), campo)


def de_desenho(geometria: dict) -> dict:
    validar(geometria, "geometria")
    prov = {"fonte": "Desenho do produtor no mapa", "obtido_em": dt.date.today().isoformat()}
    return {"candidato": car.candidato(geometria, "desenho", prov), "avisos": []}


def de_arquivo(conteudo: bytes, nome: str) -> dict:
    lim = limites()
    try:
        geom, info = arquivos.ler(conteudo, nome, lim["arquivo_formatos"]["valor"], lim["arquivo_max_bytes"]["valor"])
    except arquivos.ErroArquivo as e:
        raise car.ErroCar(e.codigo, e.mensagem, "arquivo", status=413 if e.codigo == "arquivo_grande" else 422)
    validar(geom, "arquivo")
    prov = {"fonte": f"Arquivo enviado pelo produtor ({info['nome_formato']})", "arquivo": nome, "formato": info["formato"],
            "obtido_em": dt.date.today().isoformat()}
    return {"candidato": car.candidato(geom, "arquivo", prov), "arquivo": info, "avisos": []}
