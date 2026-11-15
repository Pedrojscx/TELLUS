"""Carga somente leitura das referências versionadas em referencias/localizacao/."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
DIR_PADRAO = RAIZ / "referencias" / "localizacao"


@dataclass(frozen=True)
class Procedencia:
    fonte: str
    url: str
    obtido_em: str
    status: str = "fonte"

    def como_dict(self) -> dict:
        return {"fonte": self.fonte, "url": self.url, "obtido_em": self.obtido_em, "status": self.status}


@dataclass(frozen=True)
class Referencias:
    municipios: dict[str, dict]
    malha: dict[str, dict]  # codigo_ibge -> geometria
    brasil: dict  # geometria do país
    estacoes: list[dict]
    pracas: list[dict]
    limites: dict
    procedencias: dict[str, Procedencia]
    versao: str
    municipios_ordenados: list[dict] = field(default_factory=list)

    def limite(self, nome: str) -> float:
        return float(self.limites[nome]["valor"])


def _ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _procedencias(fonte_md: str) -> tuple[dict[str, Procedencia], str]:
    """Lê a tabela do FONTE.md: | arquivo bruto | fonte | url | obtido em |."""
    proc: dict[str, Procedencia] = {}
    for linha in fonte_md.splitlines():
        partes = [p.strip() for p in linha.strip().strip("|").split("|")]
        if len(partes) == 4 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", partes[3]):
            proc[partes[0]] = Procedencia(fonte=partes[1], url=partes[2], obtido_em=partes[3])
    m = re.search(r"versao_referencias:\s*(\d{4}-\d{2}-\d{2})", fonte_md)
    versao = m.group(1) if m else max(p.obtido_em for p in proc.values())
    return proc, versao


@lru_cache(maxsize=4)
def carregar(diretorio: str | None = None) -> Referencias:
    d = Path(diretorio or os.environ.get("TELLUS_REF_LOCALIZACAO", DIR_PADRAO))
    municipios = {m["codigo_ibge"]: m for m in _ler(d / "municipios.json")}
    malha = {f["properties"]["codarea"]: f["geometry"] for f in _ler(d / "malha_municipios.geojson")["features"]}
    brasil = _ler(d / "brasil.geojson")["features"][0]["geometry"]
    procedencias, versao = _procedencias((d / "FONTE.md").read_text(encoding="utf-8"))
    return Referencias(
        municipios=municipios,
        malha=malha,
        brasil=brasil,
        estacoes=_ler(d / "estacoes_inmet.json"),
        pracas=_ler(d / "pracas_conab.json"),
        limites=_ler(d / "limites.json"),
        procedencias=procedencias,
        versao=versao,
        municipios_ordenados=sorted(
            (m for m in municipios.values() if m.get("centroide")),
            key=lambda m: (m["nome_normalizado"], m["uf"]),
        ),
    )
