"""Regras puras do contrato: validação do pedido, cobertura de proveniência, estado geral e hash."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from tellus.car import regras as car_regras

from . import versao
from .modelos import PedidoCalculo

RAIZ = Path(__file__).resolve().parents[4]
CAMPOS_PROVENIENCIA = ("fonte", "versao", "periodo", "unidade", "localizacao", "qualidade")


def hash_estavel(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- limites (D-009)


@lru_cache(maxsize=1)
def limites() -> dict:
    """Arquivo único de limites (D-009, hipótese operacional; ver limites.json)."""
    return json.loads((Path(__file__).parent / "limites.json").read_text(encoding="utf-8"))


def _total_vertices(geom: Mapping) -> int:
    return sum(len(anel) for pol in car_regras.poligonos(dict(geom)) for anel in pol)


def validar_geometria(geom: Mapping) -> list[str]:
    if not isinstance(geom, Mapping) or geom.get("type") not in ("Polygon", "MultiPolygon"):
        return ["a geometria precisa ser um GeoJSON Polygon ou MultiPolygon"]
    lim = limites()
    motivos = car_regras.validar_poligono(dict(geom), lim["vertices_por_anel_max"]["valor"])
    if motivos:
        return motivos
    return []


def limites_excedidos(geom: Mapping) -> list[tuple[str, str]]:
    """D-009: vértices totais e área. Nunca simplifica: devolve (código, mensagem) para o produtor agir."""
    lim, saida = limites(), []
    n, nmax = _total_vertices(geom), lim["vertices_total_max"]["valor"]
    if n > nmax:
        saida.append(("vertices_excedidos", f"A geometria tem {n} vértices; o limite é {nmax}. Simplifique o contorno ou divida a área em partes."))
    a, amax = car_regras.area_ha(dict(geom)), lim["area_max_ha"]["valor"]
    if a > amax:
        saida.append(("area_excedida", f"A área tem {a:,.0f} ha; o limite é {amax:,.0f} ha. Divida a área em lavouras menores.".replace(",", ".")))
    return saida


# ---------------------------------------------------------------- pedido (#96)


def _mensagens(e: ValidationError) -> list[str]:
    saida = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err.get("loc", ()) if not str(x).startswith("function-after"))
        msg = str(err.get("msg", "")).removeprefix("Value error, ")
        saida.append(f"{loc}: {msg}" if loc else msg)
    return saida


def normalizar_pedido(bruto: Mapping) -> dict:
    """Versão → modelo → geometria. Qualquer falha vira ErroContrato e o cálculo não começa."""
    if not isinstance(bruto, Mapping):
        raise versao.ErroContrato("pedido_invalido", "O pedido precisa ser um objeto JSON.")
    versao.verificar(bruto.get("versao_contrato"))
    try:
        p = PedidoCalculo.model_validate(dict(bruto))
    except ValidationError as e:
        msgs = _mensagens(e)
        campo = msgs[0].split(":", 1)[0] if msgs and ":" in msgs[0] else None
        raise versao.ErroContrato("pedido_invalido", "Pedido inválido: " + "; ".join(msgs), campo=campo, detalhes=msgs) from e
    if p.area.tipo == "geometria":
        motivos = validar_geometria(p.area.geometria)
        if motivos:
            raise versao.ErroContrato("geometria_invalida", "Geometria inválida; o cálculo não foi iniciado: " + "; ".join(motivos),
                                      campo="area.geometria", detalhes=motivos)
        excedidos = limites_excedidos(p.area.geometria)
        if excedidos:
            raise versao.ErroContrato(excedidos[0][0], " ".join(m for _, m in excedidos), campo="geometria",
                                      detalhes=[m for _, m in excedidos])
    d = p.model_dump(mode="json")
    return d | {"hash_pedido": hash_estavel(d)}


# ---------------------------------------------------------------- proveniência (#97, SC-002)


def numeros(obj, caminho: str = "") -> Iterator[tuple[str, float]]:
    """(caminho, número) de cada número; índices de lista viram '*'. Booleanos não são números."""
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        yield caminho, obj
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            yield from numeros(v, f"{caminho}.{k}" if caminho else str(k))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from numeros(v, f"{caminho}.*" if caminho else "*")


def proveniencia_completa(p: Mapping) -> bool:
    return all(isinstance(p.get(c), str) and p[c].strip() for c in CAMPOS_PROVENIENCIA) and bool(p.get("cobre"))


def _secoes(resposta: Mapping) -> Iterable[tuple[str, Mapping]]:
    for i, b in enumerate(resposta.get("culturas") or []):
        for nome in ("risco_hidrico", "economia"):
            yield f"culturas.{i}.{nome}", b[nome]
    if resposta.get("recomendacao"):
        yield "recomendacao", resposta["recomendacao"]


def numeros_sem_proveniencia(resposta: Mapping) -> list[str]:
    """Todo número de `conteudo` de seção precisa de um padrão `cobre` numa proveniência completa.

    Também confere que nenhuma proveniência da seção está incompleta. Os contextos 009/010 ficam de
    fora (proveniência própria, verificada nas specs 009/010).
    """
    falhas = []
    for nome, s in _secoes(resposta):
        provs = s.get("proveniencia") or []
        for p in provs:
            if not proveniencia_completa(p):
                falhas.append(f"{nome}: proveniência '{p.get('id')}' incompleta")
        padroes = [c for p in provs if proveniencia_completa(p) for c in p["cobre"]]
        for caminho, v in numeros(s.get("conteudo") or {}):
            if not any(fnmatch.fnmatchcase(caminho, pad) for pad in padroes):
                falhas.append(f"{nome}.conteudo.{caminho} = {v} sem proveniência")
    return falhas


# ---------------------------------------------------------------- estado geral (#98)


def estado_geral(secoes: Iterable[Mapping], fontes: Iterable[Mapping]) -> str:
    """erro > incompleto > final_com_cache > final. Parcial nunca é final."""
    obr = [s for s in secoes if s["obrigatoria"]]
    if any(s["estado"] == "erro" for s in obr):
        return "erro"
    if any(s["estado"] in ("pendente", "indisponivel") for s in obr):
        return "incompleto"
    if any(f["estado"] == "cache" for f in fontes):
        return "final_com_cache"
    return "final"
