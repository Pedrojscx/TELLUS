"""Versão do contrato e regra de compatibilidade (#55, FR-001).

MAIOR: remover/renomear campo, mudar tipo, unidade ou significado de estado.
MENOR: campo opcional novo ou seção nova (ex.: a 008). CORREÇÃO: texto, sem efeito no formato.
O servidor aceita pedidos do mesmo MAIOR com MENOR ≤ o seu.
"""

from __future__ import annotations

import re

VERSAO = "1.1.0"  # 1.1.0: seção recomendacao (008) com conteúdo; origem_informada/data_informada nas premissas
REGRA = ("Aceita pedidos com o mesmo número MAIOR e MENOR menor ou igual ao do servidor. "
         "Mudança incompatível (remover/renomear campo, mudar tipo, unidade ou significado) sobe o MAIOR.")
_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class ErroContrato(Exception):
    def __init__(self, codigo: str, mensagem: str, origem: str = "pedido", campo: str | None = None,
                 status: int = 422, versoes_aceitas: list[str] | None = None, detalhes: list[str] | None = None):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.origem, self.campo = codigo, mensagem, origem, campo
        self.status, self.versoes_aceitas, self.detalhes = status, versoes_aceitas, detalhes

    def como_dict(self) -> dict:
        d = {"codigo": self.codigo, "mensagem": self.mensagem, "origem": self.origem, "campo": self.campo}
        if self.versoes_aceitas is not None:
            d["versoes_aceitas"] = self.versoes_aceitas
        if self.detalhes:
            d["detalhes"] = self.detalhes
        return d


def _partes(v: str) -> tuple[int, int, int] | None:
    m = _SEMVER.match(v or "")
    return tuple(int(x) for x in m.groups()) if m else None  # type: ignore[return-value]


def versoes_aceitas() -> list[str]:
    maior, menor, _ = _partes(VERSAO)  # type: ignore[misc]
    return [f"{maior}.{m}.x" for m in range(menor + 1)]


def verificar(v: str | None) -> str:
    """Devolve a versão se compatível; senão ErroContrato `versao_incompativel` com as versões aceitas."""
    if v is None:
        raise ErroContrato("versao_ausente", f"Informe versao_contrato (versão atual {VERSAO}).", campo="versao_contrato",
                           versoes_aceitas=versoes_aceitas())
    p, s = _partes(v), _partes(VERSAO)
    if p is None:
        raise ErroContrato("versao_invalida", f"versao_contrato '{v}' não segue MAIOR.MENOR.CORREÇÃO.", campo="versao_contrato",
                           versoes_aceitas=versoes_aceitas())
    if p[0] != s[0] or p[1] > s[1]:
        raise ErroContrato("versao_incompativel", f"O servidor fala o contrato {VERSAO} e não aceita a versão {v}. "
                           f"Versões aceitas: {', '.join(versoes_aceitas())}.", campo="versao_contrato",
                           versoes_aceitas=versoes_aceitas())
    return v
