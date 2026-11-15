"""Consulta CAR → estado + candidato; upload SICAR → candidato; confirmação → lavoura (data-model)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tellus.localizacao.referencias import carregar as carregar_loc
from tellus.localizacao.servico import ErroLocalizacao, resolver

from . import regras, shapefile, wfs

RAIZ = Path(__file__).resolve().parents[4]
LIMITES = json.loads((RAIZ / "referencias" / "car" / "limites.json").read_text(encoding="utf-8"))
# Limite técnico por anel (spec 001), lido do arquivo único de limites (D-009); o valor não mudou.
LIMITES_UNICOS = json.loads((RAIZ / "backend" / "src" / "tellus" / "contrato" / "limites.json").read_text(encoding="utf-8"))
MAX_VERTICES = int(LIMITES_UNICOS["vertices_por_anel_max"]["valor"])
CASAS = int(LIMITES["casas_decimais_id"]["valor"])

MSG_UPLOAD = (
    "Você pode enviar o shapefile do imóvel exportado do SICAR (.zip com .shp, .shx, .dbf e .prj) "
    "ou desenhar a área no mapa."
)
AVISO_DECLARADO = (
    "O limite vem do CAR, declarado pelo proprietário; não é medição. Confira antes de confirmar."
)


class ErroCar(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None, status: int = 422):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.campo, self.status = codigo, mensagem, campo, status


def _aviso(codigo: str, mensagem: str) -> dict:
    return {"codigo": codigo, "mensagem": mensagem}


def candidato(geom: dict, origem: str, proveniencia: dict) -> dict:
    ref = carregar_loc()
    can = regras.canonica(geom, CASAS)
    lat, lon = regras.centroide_bbox(can)
    return {
        "id_geometria": regras.id_geometria(can, CASAS),
        "geometria": can,
        "origem": origem,
        "area_ha": round(regras.area_ha(can), 2),
        "municipios": regras.municipios_atingidos(can, ref.municipios, ref.malha),
        "centroide": {"lat": round(lat, 6), "lon": round(lon, 6)},
        "estado": "aguardando_confirmacao",
        "proveniencia": proveniencia,
    }


def consultar(codigo_informado: str, dir_cache: Path | None = None, cliente=None) -> dict:
    codigo = regras.normalizar_codigo(codigo_informado)
    base = {
        "codigo_informado": codigo_informado,
        "codigo": codigo,
        "proveniencia": None,
        "qualidade": None,
        "candidato": None,
        "alternativa": None,
        "avisos": [],
        "erros_geometria": [],
    }
    if codigo is None:
        return base | {
            "estado": "codigo_invalido",
            "consultado_em": None,
            "mensagem": "O número do CAR deve ter o formato UF-0000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "
                        "(sigla da UF, código IBGE do município e 32 letras/números).",
        }
    avisos = []
    try:
        corpo, meta = wfs.consultar(codigo, dir_cache, cliente)
    except wfs.FonteIndisponivel as e:
        cache = wfs.ler_cache(codigo, dir_cache)
        if cache is None:
            return base | {
                "estado": "fonte_indisponivel",
                "consultado_em": None,
                "mensagem": f"Não foi possível consultar o CAR agora: {e}. Fonte: {wfs.URL}.",
                "alternativa": {"upload_sicar": True, "mensagem": MSG_UPLOAD},
            }
        corpo, meta = cache
        avisos.append(_aviso("cache_usado", f"O WFS do SICAR não respondeu; usando a consulta guardada de {meta.get('obtido_em')}."))
    prov = {"fonte": "SICAR — Cadastro Ambiental Rural (WFS público)", "versao": wfs.VERSAO, "url": meta.get("url", wfs.URL),
            "camada": meta.get("camada", wfs.camada(codigo)), "obtido_em": meta.get("obtido_em")}
    base |= {"proveniencia": prov, "consultado_em": meta.get("obtido_em"), "avisos": avisos}
    feicoes = corpo.get("features") or []
    if not feicoes:
        return base | {
            "estado": "inexistente",
            "mensagem": "Nenhum imóvel com esse número no CAR público.",
            "alternativa": {"upload_sicar": True, "mensagem": MSG_UPLOAD},
        }
    f = feicoes[0]
    p = f.get("properties") or {}
    base["qualidade"] = {
        "condicao": p.get("condicao"),
        "status_imovel": p.get("status_imovel"),
        "data_atualizacao": (p.get("data_atualizacao") or "")[:10] or None,
        "tipo_imovel": p.get("tipo_imovel"),
        "area_declarada_ha": p.get("area"),
        "municipio_car": p.get("municipio"),
        "cod_municipio_ibge": p.get("cod_municipio_ibge"),
    }
    geom = f.get("geometry")
    if not geom:
        return base | {
            "estado": "sem_geometria",
            "mensagem": "O imóvel existe no CAR, mas a resposta não trouxe o limite.",
            "alternativa": {"upload_sicar": True, "mensagem": MSG_UPLOAD},
        }
    erros = regras.validar_poligono(geom, MAX_VERTICES)
    if erros:
        return base | {
            "estado": "geometria_invalida",
            "erros_geometria": erros,
            "mensagem": "O limite do imóvel no CAR não é uma área válida para cálculo.",
            "alternativa": {"upload_sicar": True, "mensagem": MSG_UPLOAD},
        }
    base["avisos"] = avisos + [_aviso("limite_declarado", AVISO_DECLARADO)]
    return base | {
        "estado": "encontrado",
        "mensagem": "Imóvel encontrado no CAR. Confira o limite no mapa e confirme.",
        "candidato": candidato(geom, "car", prov | {"codigo_car": codigo}),
    }


def upload_sicar(conteudo: bytes, nome_arquivo: str = "") -> dict:
    try:
        geoms, info = shapefile.ler_zip(conteudo)
    except shapefile.ErroArquivo as e:
        raise ErroCar(e.codigo, e.mensagem, "arquivo")
    geom = geoms[0] if len(geoms) == 1 else regras.uniao(geoms)
    erros = regras.validar_poligono(geom, MAX_VERTICES)
    if erros:
        raise ErroCar("geometria_invalida", "A geometria do arquivo não é válida: " + "; ".join(erros), "arquivo")
    avisos = []
    if len(geoms) > 1:
        avisos.append(_aviso("varias_feicoes", f"O arquivo tem {len(geoms)} polígonos; foram unidos numa área só."))
    prov = {"fonte": "Arquivo enviado pelo produtor (shapefile exportado do SICAR)", "arquivo": nome_arquivo,
            "obtido_em": dt.date.today().isoformat()}
    return {"candidato": candidato(geom, "upload_sicar", prov), "arquivo": info, "avisos": avisos}


def confirmar(geometria: dict, id_geometria: str, origem: str, proveniencia: dict | None = None) -> dict:
    erros = regras.validar_poligono(geometria, MAX_VERTICES)
    if erros:
        raise ErroCar("geometria_invalida", "Geometria inválida: " + "; ".join(erros), "geometria")
    if origem in ("desenho", "arquivo"):  # spec 002: limites da D-009 também na confirmação (CAR e SICAR inalterados)
        from tellus.contrato.regras import limites_excedidos

        excedidos = limites_excedidos(geometria)
        if excedidos:
            raise ErroCar(excedidos[0][0], " ".join(m for _, m in excedidos), "geometria")
    if regras.id_geometria(geometria, CASAS) != id_geometria:
        raise ErroCar("geometria_alterada", "A geometria enviada não é a mesma que foi conferida. Confira de novo.", "id_geometria")
    can = candidato(geometria, origem, proveniencia or {})
    lat, lon = can["centroide"]["lat"], can["centroide"]["lon"]
    try:
        loc = resolver(carregar_loc(), lat, lon, meio="mapa")
    except ErroLocalizacao as e:
        raise ErroCar(e.codigo, e.mensagem, "geometria")
    return can | {"estado": "confirmada", "confirmada_em": dt.date.today().isoformat(), "localizacao": loc}
