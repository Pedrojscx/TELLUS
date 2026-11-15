"""Modelos do contrato 1.1.0 (data-model.md). Pedido (#96) e resposta (#97, #98, #99)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .versao import VERSAO

Cultura = Literal["milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura"]
CULTURAS: tuple[str, ...] = ("milho_2a_safra", "sorgo_granifero_2a_safra", "braquiaria_cobertura")


class _Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- pedido (#96)


class AreaPonto(_Estrito):
    tipo: Literal["ponto"]
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    confirmada: bool
    codigo_ibge: str | None = None


class AreaGeometria(_Estrito):
    tipo: Literal["geometria"]
    geometria: dict[str, Any]
    id_geometria: str = Field(min_length=1)
    origem: Literal["car", "upload_sicar", "desenho", "arquivo"]
    confirmada: bool


class Solo(_Estrito):
    textura: Literal["arenosa", "media", "argilosa"] | None = None
    cad_mm: float | None = Field(default=None, gt=0)
    classe: str | None = None
    granulometria: dict[str, float] | None = None

    @model_validator(mode="after")
    def _um_modo(self) -> "Solo":
        modos = [k for k in ("textura", "cad_mm", "classe", "granulometria") if getattr(self, k) is not None]
        if len(modos) != 1:
            raise ValueError("solo: informe exatamente um entre textura, cad_mm, classe ou granulometria")
        if self.granulometria is not None:
            if set(self.granulometria) != {"areia", "silte", "argila"} or abs(sum(self.granulometria.values()) - 100) > 0.5:
                raise ValueError("solo.granulometria: areia, silte e argila em % somando 100")
        return self


PREMISSAS_DE_PRECO = {("economia", "preco_r_saca")}  # onde a cotação informada (1.1.0) é aceita


class PremissaEditada(_Estrito):
    modulo: Literal["motor", "culturas", "economia"]
    id: str = Field(min_length=1)
    valor_novo: float
    unidade: str = Field(min_length=1)
    cultura: Cultura | None = None  # None = vale para todas as culturas calculadas
    valor_padrao: float | None = None  # preenchido na resposta; o pedido pode omitir
    # 1.1.0 (D-005): cotação local rastreável, ex.: sorgo sem indicador CEPEA. Só em premissa de preço, os dois juntos.
    origem_informada: str | None = None
    data_informada: dt.date | None = None

    @model_validator(mode="after")
    def _cotacao(self) -> "PremissaEditada":
        if self.origem_informada is None and self.data_informada is None:
            return self
        if (self.modulo, self.id) not in PREMISSAS_DE_PRECO:
            raise ValueError("origem_informada/data_informada só valem para a premissa de preço (economia.preco_r_saca)")
        if self.origem_informada is None or self.data_informada is None:
            raise ValueError("informe origem_informada e data_informada juntas (cotação rastreável)")
        origem = " ".join(self.origem_informada.split())
        if not origem:
            raise ValueError("origem_informada não pode ser vazia")
        if self.data_informada > dt.date.today():
            raise ValueError("data_informada não pode ser no futuro")
        self.origem_informada = origem
        return self


class Contextos(_Estrito):
    vegetacao: bool = False
    umidade: bool = False


class PedidoCalculo(_Estrito):
    versao_contrato: str
    area: AreaPonto | AreaGeometria = Field(discriminator="tipo")
    data_colheita_soja: dt.date
    solo: Solo
    grupo: Literal["GRUPO I", "GRUPO II", "GRUPO III", "nao_sei"]
    metodologia: Literal["cultura_escolhida", "comparar_alternativas"]
    cultura: Cultura | None = None
    premissas_editadas: list[PremissaEditada] = []
    contextos: Contextos = Contextos()

    @model_validator(mode="after")
    def _regras(self) -> "PedidoCalculo":
        if not self.area.confirmada:
            raise ValueError("area: a área precisa estar confirmada pelo produtor antes do cálculo")
        if self.metodologia == "cultura_escolhida" and self.cultura is None:
            raise ValueError("cultura: obrigatória na metodologia cultura_escolhida")
        if self.metodologia == "comparar_alternativas" and self.cultura is not None:
            raise ValueError("cultura: não se informa cultura em comparar_alternativas")
        chaves = [(p.modulo, p.id, p.cultura) for p in self.premissas_editadas]
        if len(chaves) != len(set(chaves)):
            raise ValueError("premissas_editadas: premissa repetida")
        return self


# ---------------------------------------------------------------- resposta (#97, #98, #99)


class Proveniencia(_Estrito):
    """Os seis campos da constituição (Princípio I) + o que esta proveniência explica (`cobre`)."""

    id: str
    fonte: str
    versao: str
    periodo: str
    unidade: str
    localizacao: str
    qualidade: str
    situacao: Literal["fonte", "cache", "hipotese", "editado", "calculado", "pedido", "nao_se_aplica",
                      "informada_pelo_produtor"]  # 1.1.0
    url: str | None = None
    obtido_em: str | None = None
    cobre: list[str] = Field(min_length=1)

    @field_validator("fonte", "versao", "periodo", "unidade", "localizacao", "qualidade")
    @classmethod
    def _nao_vazio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("campo de proveniência vazio")
        return v


class Aviso(_Estrito):
    tipo: Literal["aviso"] = "aviso"
    codigo: str
    mensagem: str
    origem: str


class CacheInfo(_Estrito):
    disponivel: bool
    obtido_em: str | None = None


class ErroFonte(_Estrito):
    tipo: Literal["erro"] = "erro"
    codigo: str
    mensagem: str
    origem: str
    campo: str | None = None
    cache: CacheInfo = CacheInfo(disponivel=False)
    acao: str | None = None


class EstadoFonte(_Estrito):
    fonte: str
    estado: Literal["ok", "cache", "falha"]
    obtido_em: str | None = None
    secao: str


class Secao(_Estrito):
    id: Literal["risco_hidrico", "economia", "recomendacao"]
    spec: str
    obrigatoria: bool
    estado: Literal["disponivel", "indisponivel", "pendente", "erro"]
    versao_modulo: str | None
    conteudo: dict[str, Any] | None
    proveniencia: list[Proveniencia]
    avisos: list[Aviso] = []
    erro: ErroFonte | None = None

    @model_validator(mode="after")
    def _coerente(self) -> "Secao":
        if self.estado == "disponivel" and self.conteudo is None:
            raise ValueError("seção disponível sem conteúdo")
        if self.estado == "erro" and self.erro is None:
            raise ValueError("seção em erro sem ErroFonte")
        if self.estado == "pendente" and self.conteudo is not None:
            raise ValueError("seção pendente não tem conteúdo (nada é inventado)")
        return self


class BlocoCultura(_Estrito):
    cultura: Cultura
    risco_hidrico: Secao
    economia: Secao


class ContextoOpcional(_Estrito):
    id: Literal["vegetacao", "umidade"]
    spec: str
    estado: Literal["disponivel", "indisponivel", "erro", "nao_solicitado"]
    conteudo: dict[str, Any] | None = None
    avisos: list[dict[str, Any]] = []
    erro: ErroFonte | None = None


class Versoes(_Estrito):
    contrato: str
    hash_pedido: str
    hash_principal: str
    modulos: dict[str, str | None]


class RespostaCalculo(_Estrito):
    versao_contrato: str = VERSAO
    pedido: dict[str, Any]
    estado_geral: Literal["final", "final_com_cache", "incompleto", "erro"]
    final: bool
    culturas: list[BlocoCultura]
    recomendacao: Secao
    contextos: dict[Literal["vegetacao", "umidade"], ContextoOpcional]
    fontes: list[EstadoFonte]
    avisos: list[Aviso]
    erros: list[ErroFonte]
    hipoteses: list[str]
    premissas_editadas: list[PremissaEditada]
    versoes: Versoes

    @model_validator(mode="after")
    def _final_coerente(self) -> "RespostaCalculo":
        if self.final != (self.estado_geral in ("final", "final_com_cache")):
            raise ValueError("final precisa refletir estado_geral")
        return self
