"""Cliente do SISZARC (MAPA), sem login: percorre os combos do formulário e baixa o relatório XLS.

Um relatório = safra × cultura × UF × grupo de cultivar (todos os solos e municípios da UF).
Sequência documentada na spec 004 (14/11) e conferida em 15/11.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path

import httpx
import xlrd

BASE = "https://sistemasweb.agricultura.gov.br/siszarc/"
PAGINA = BASE + "gerarRelatorioPublicacoesDoZarc.action"
F = "form.filtroConsulta."
CAMPOS = [
    F + "anoSafra", F + "cultura.codigoCultura", F + "tipoSistemaCultivo.cdTipoCultivo",
    F + "tipoClimaCultivo.idTipoClima", F + "sgUF", F + "numeroPortaria", F + "grupo.cdGrupo", F + "solo.cdSolo",
]
ACOES = [
    "carregarComboCulturas", "carregarComboOutrosManejos", "carregarComboClima", "carregarComboUfs",
    "carregarComboPortarias", "carregarComboGrupos", "carregarComboSolos",
]
SEQUEIRO = "1"
CLIMA_NAO_SE_APLICA = "0"


class ErroSiszarc(Exception):
    pass


def _opcoes(pagina: str, nome: str) -> list[tuple[str, str]]:
    m = re.search(r'<select name="' + re.escape(nome) + r'"[^>]*>(.*?)</select>', pagina, re.S)
    if not m:
        return []
    return [
        (html.unescape(v), html.unescape(t).strip())
        for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', m.group(1))
        if v
    ]


class Sessao:
    def __init__(self, cliente: httpx.Client | None = None):
        self.cli = cliente or httpx.Client(headers={"User-Agent": "Mozilla/5.0 (TELLUS)"}, timeout=120, follow_redirects=True)
        self.valores = {c: "" for c in CAMPOS} | {"isRelatorio": "false", "form.versaoPortaria": "Atual"}
        try:
            self.pagina = self.cli.get(PAGINA).text
        except httpx.HTTPError as e:
            raise ErroSiszarc(f"SISZARC sem resposta ({type(e).__name__})") from e

    def escolher(self, nivel: int, valor: str) -> list[tuple[str, str]]:
        """Define o campo `nivel` e devolve as opções do próximo combo."""
        self.valores[CAMPOS[nivel]] = valor
        for c in CAMPOS[nivel + 1:]:
            self.valores[c] = ""
        if nivel < len(ACOES):
            try:
                self.pagina = self.cli.post(BASE + f"gerarRelatorioPublicacoesDoZarc!{ACOES[nivel]}.action", data=self.valores).text
            except httpx.HTTPError as e:
                raise ErroSiszarc(f"SISZARC falhou em {ACOES[nivel]} ({type(e).__name__})") from e
            return _opcoes(self.pagina, CAMPOS[nivel + 1])
        return []

    def opcoes(self, nivel: int) -> list[tuple[str, str]]:
        return _opcoes(self.pagina, CAMPOS[nivel])

    def xls(self) -> bytes:
        dados = self.valores | {"isRelatorio": "true"}
        try:
            r = self.cli.post(BASE + "gerarRelatorioPublicacoesDoZarc!gerarRelatorioXLS.action", data=dados)
        except httpx.HTTPError as e:
            raise ErroSiszarc(f"SISZARC falhou ao gerar o XLS ({type(e).__name__})") from e
        if not r.content.startswith(b"\xd0\xcf\x11\xe0"):
            raise ErroSiszarc("SISZARC não devolveu uma planilha XLS")
        return r.content


def baixar_relatorios(dir_cache: Path, safra: str, codigo_cultura: str, uf: str) -> list[Path]:
    """Baixa um XLS por portaria × grupo disponível para a cultura e UF. Devolve os caminhos."""
    s = Sessao()
    s.escolher(0, safra)
    s.escolher(1, codigo_cultura)
    s.escolher(2, SEQUEIRO)
    ufs = [v for v, _ in s.escolher(3, CLIMA_NAO_SE_APLICA)]
    if uf not in ufs:
        return []
    caminhos = []
    for portaria, _ in s.escolher(4, uf):
        for grupo, nome_grupo in s.escolher(5, portaria):
            s.escolher(6, grupo)  # carrega solos; solo vazio = todos
            conteudo = s.xls()
            nome = f"{safra.replace(' / ', '-')}_{codigo_cultura}_{uf}_{portaria}_{grupo}.xls"
            p = dir_cache / nome
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(conteudo)
            meta = {
                "url": PAGINA,
                "acao": "gerarRelatorioPublicacoesDoZarc!gerarRelatorioXLS.action",
                "filtros": {"safra": safra, "cultura": codigo_cultura, "manejo": "Sequeiro", "uf": uf,
                            "portaria": portaria, "grupo": nome_grupo, "solo": "todos"},
                "obtido_em": dt.date.today().isoformat(),
                "sha256": hashlib.sha256(conteudo).hexdigest(),
            }
            p.with_suffix(".xls.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            caminhos.append(p)
            s.escolher(4, uf)  # volta para listar grupos de novo
            s.escolher(5, portaria)
    return caminhos


def ler_relatorio(conteudo: bytes) -> list[dict]:
    """Linhas do relatório: safra, cultura, uf, portaria, data_portaria, municipio, grupo, solo, riscos[36]."""
    s = xlrd.open_workbook(file_contents=conteudo).sheet_by_index(0)
    cab = None
    linhas = []
    for i in range(s.nrows):
        v = [str(x).strip() for x in s.row_values(i)]
        if cab is None:
            if "Safra" in v and "Dec 1" in v:
                cab = {nome: j for j, nome in enumerate(v) if nome}
                rotulos = v[cab["Dec 1"]:cab["Dec 1"] + 36]
                if len(rotulos) != 36 or any(not re.fullmatch(r"De[cv] %d" % (k + 1), r) for k, r in enumerate(rotulos)):
                    raise ErroSiszarc(f"colunas de decêndio inesperadas no relatório: {rotulos}")
            continue
        if not v[cab["Safra"]]:
            continue
        # pela posição: o relatório oficial tem rótulo errado ("Dev 35") na coluna do decêndio 35
        riscos = [int(float(b)) if b else 0 for b in v[cab["Dec 1"]:cab["Dec 1"] + 36]]
        linhas.append({
            "safra": v[cab["Safra"]],
            "cultura": v[cab["Cultura"]],
            "uf": v[cab["UF"]],
            "portaria": v[cab["Portaria"]].split(".")[0],
            "data_portaria": v[cab["Data Portaria"]],
            "municipio": v[cab["Município"]] if "Município" in cab else v[cab[next(k for k in cab if k.startswith("Munic"))]],
            "grupo": v[cab["Grupo"]],
            "solo": v[cab["Solo"]],
            "riscos": riscos,
        })
    if cab is None:
        raise ErroSiszarc("relatório XLS sem o cabeçalho esperado (Safra, Dec 1…)")
    return linhas
