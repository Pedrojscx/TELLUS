"""Monta o contexto regional de umidade SMAP (spec 010, #53, #93, #94, #95).

D-008 (#70) segue aberta. O usuário propôs uma HIPÓTESE OPERACIONAL para o protótipo, que não é
parâmetro científico validado:
- Produto SPL3SMP_E (L3 Enhanced, EASE-Grid 2.0 de 9 km, superfície de ≈ 0–5 cm): `PRODUTO_HIPOTESE`.
- Período: observações VÁLIDAS dos últimos `JANELA_DIAS` = 30 dias, com a data de cada uma e a
  contagem de válidas.
As duas aparecem como `hipotese` na resposta e mudam por parâmetro. Com `data` ou `inicio`/`fim`,
cada dia do pedido aparece separado, sem média.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from collections.abc import Callable
from pathlib import Path

from tellus.localizacao.servico import validar_coordenadas

from . import cliente, regras

RAIZ = Path(__file__).resolve().parents[4]
DIR_CACHE = Path(os.environ.get("TELLUS_CACHE_UMIDADE", RAIZ / "data" / "raw" / "umidade"))
FICHA = RAIZ / "referencias" / "umidade" / "produtos.json"
PRODUTO_HIPOTESE = "SPL3SMP_E"  # hipótese operacional do protótipo (#70), NÃO é decisão aprovada
JANELA_DIAS = 30  # hipótese operacional do protótipo (#70), parametrizável
MAX_DIAS = 31  # limite de tamanho da resposta (não é regra agronômica)

Buscar = Callable[[str, dict, str, int, int, dt.date, dt.date], object]


class ErroUmidade(Exception):
    def __init__(self, codigo: str, mensagem: str, origem: str, status: int = 404):
        super().__init__(mensagem)
        self.codigo, self.mensagem, self.origem, self.status = codigo, mensagem, origem, status


def ficha() -> dict:
    return json.loads(FICHA.read_text(encoding="utf-8"))


def _origem(produto: str, f: dict) -> str:
    return f"NASA SMAP {produto} V{f['versao']} (NSIDC DAAC)"


def produtos() -> dict:
    """Candidatos da ficha, todos com a decisão pendente (para a tela da spec 012)."""
    fi = ficha()
    return {
        "decisao": regras.DECISAO_PRODUTO,
        "hipotese_em_uso": PRODUTO_HIPOTESE,
        "natureza": regras.NATUREZA,
        "uso": regras.USO,
        "produtos": [
            {"id": k, "titulo": v["titulo"], "versao": v["versao"], "nivel": v["nivel"], "natureza": v["natureza"],
             "resolucao_espacial": v["resolucao_espacial"], "resolucao_temporal": v["resolucao_temporal"],
             "camada_solo": v["camada_solo"], "variantes": sorted(v["variaveis"]), "doi": v["doi"],
             "situacao": regras.DECISAO_PRODUTO["estado"]}
            for k, v in sorted(fi["produtos"].items())
        ],
        "obtido_em": fi["obtido_em"],
    }


def _datas(data: str | None, inicio: str | None, fim: str | None) -> tuple[dt.date, dt.date] | None:
    try:
        if data:
            d = dt.date.fromisoformat(data)
            return d, d
        if inicio or fim:
            a = dt.date.fromisoformat(inicio or fim)
            b = dt.date.fromisoformat(fim or inicio)
            if b < a:
                raise ErroUmidade("periodo_invalido", "O fim do período vem antes do início.", "pedido", 422)
            if (b - a).days + 1 > MAX_DIAS:
                raise ErroUmidade("periodo_invalido", f"Peça no máximo {MAX_DIAS} dias por vez.", "pedido", 422)
            return a, b
    except ValueError:
        raise ErroUmidade("periodo_invalido", "Use datas no formato AAAA-MM-DD.", "pedido", 422)
    return None


def _item_indisponivel(motivo: str, base: dict, periodo: dict) -> dict:
    return regras.item_contexto(estado="indisponivel", valor=None, motivo=motivo, periodo=periodo,
                                qualidade={"flag": None, "recomendada": None, "situacao": regras.DESCONHECIDO,
                                           "texto": "Sem valor para avaliar."}, **base)


def contexto(lat=None, lon=None, produto: str | None = None, variante: str | None = None, data: str | None = None,
             inicio: str | None = None, fim: str | None = None, geometria: dict | None = None,
             dir_cache: Path | None = None, buscar: Buscar | None = None, janela_dias: int = JANELA_DIAS) -> dict:
    """Contexto regional SMAP para um ponto (lat/lon) ou geometria confirmada (spec 002/001).

    `buscar` (opcional) tenta atualizar o cache na fonte; se a fonte cair, usa o cache com aviso
    da data, ou devolve erro que nomeia a origem (Princípio VII).
    """
    dir_cache = Path(dir_cache or DIR_CACHE)
    fi = ficha()
    pedido_produto = produto
    produto = produto or PRODUTO_HIPOTESE
    if produto not in fi["produtos"]:
        raise ErroUmidade("produto_desconhecido", f"Produto SMAP '{produto}' não está na ficha de candidatos.",
                          "referencias/umidade/produtos.json", 422)
    f = fi["produtos"][produto]
    grade_id = f["grade"]
    grade = fi["grades"][grade_id]
    variantes = sorted(f["variaveis"])
    if variante and variante not in variantes:
        raise ErroUmidade("variante_desconhecida", f"Variante '{variante}' não existe em {produto}: {', '.join(variantes)}.",
                          "referencias/umidade/produtos.json", 422)
    variante_usada = variante or variantes[0]  # só no modo de dias pedidos; a janela usa todas as variantes
    periodo_pedido = _datas(data, inicio, fim)

    if geometria is not None:
        pesos = regras.celulas_da_geometria(geometria, grade["colunas"], grade["linhas"])
        if geometria["type"] == "Point":
            lon_ref, lat_ref = geometria["coordinates"][:2]
        else:
            xs = [x for a in _aneis(geometria) for x, _ in a]
            ys = [y for a in _aneis(geometria) for _, y in a]
            lat_ref, lon_ref = (min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2
        local = {"tipo": geometria["type"], "lat_referencia": round(lat_ref, 6), "lon_referencia": round(lon_ref, 6)}
    else:
        lat_ref, lon_ref = validar_coordenadas(lat, lon)
        lc = regras.celula_ease2(lat_ref, lon_ref, grade["colunas"], grade["linhas"])
        pesos = {lc: 1.0} if lc else {}
        local = {"tipo": "Point", "lat_referencia": lat_ref, "lon_referencia": lon_ref}

    produto_meta = {
        "id": produto, "titulo": f["titulo"], "nivel": f["nivel"], "natureza": f["natureza"], "doi": f["doi"],
        "situacao": regras.HIPOTESE, "decisao": regras.DECISAO_PRODUTO["id"],
        "selecionado_por": "pedido" if pedido_produto else "hipotese_operacional_do_prototipo",
    }
    resolucao = {"espacial": f["resolucao_espacial"], "temporal": f["resolucao_temporal"],
                 "camada_solo": f["camada_solo"], "situacao": regras.DOCUMENTADO, "fonte": f["documentos"][0]}
    avisos = [
        {"codigo": "contexto_regional", "mensagem": regras.USO},
        {"codigo": "decisao_pendente", "mensagem": (
            f"O produto SMAP e a regra de período ainda não foram decididos (D-008, {regras.DECISAO_PRODUTO['issue']}). "
            f"Este contexto usa {produto} ({'pedido' if pedido_produto else 'hipótese operacional do protótipo'}); "
            "produto e período são hipóteses, não parâmetros validados.")},
    ]
    itens, celulas_saida = [], []
    origem_dados, obtido, sintetico = set(), [], False

    if not pesos:
        aviso = regras.aviso_escala(f["resolucao_espacial"], f["resolucao_temporal"], None)
        base = _base(produto_meta, {"valor": f["versao"], "situacao": regras.DOCUMENTADO, "fonte": f"coleção CMR {f['concept_id']}"},
                     {"grade": grade_id, "situacao": "fora_da_grade"},
                     {"valor": f["unidade"], "situacao": regras.DOCUMENTADO, "fonte": "ficha"}, resolucao, aviso)
        itens.append(_item_indisponivel(
            "fora_da_grade: o ponto fica fora da grade EASE-Grid 2.0 global (latitude além de ≈ ±85°).", base,
            {"inicio": None, "fim": None, "variante": variante_usada}))

    for (lin, col), fracao in pesos.items():
        cel = regras.descrever_celula(*regras.centro_celula(lin, col, grade["colunas"], grade["linhas"]), grade_id, grade)
        cel["distancia_km"] = round(regras.haversine_km(lat_ref, lon_ref, cel["centro_lat"], cel["centro_lon"]), 2)
        cel |= {"fracao_da_area": fracao, "situacao": regras.CALCULADO,
                "fonte": "EASE-Grid 2.0 (EPSG:6933), referencias/umidade/FONTE.md"}
        celulas_saida.append(cel)

        falha = None
        if buscar is not None:
            a, b = periodo_pedido or (dt.date.today() - dt.timedelta(days=3),) * 2
            try:
                buscar(produto, f, grade_id, lin, col, a, b)
            except cliente.FonteIndisponivel as e:
                falha = str(e)
        lido = cliente.ler_cache(dir_cache, produto, grade_id, lin, col)
        if lido is None:
            if falha:
                raise ErroUmidade("fonte_indisponivel", f"A fonte SMAP não respondeu ({falha}) e não há cache para esta célula.",
                                  _origem(produto, f), 503)
            raise ErroUmidade("sem_cache", "Não há umidade SMAP guardada para esta célula. Rode "
                              "scripts/preparar_umidade.py com EARTHDATA_TOKEN e internet.", _origem(produto, f))
        linhas, meta = lido
        sintetico = sintetico or bool(meta.get("sintetico"))
        obtido.append(meta.get("obtido_em"))
        origem_dados.add("fixture_sintetica" if meta.get("sintetico") else "cache")
        if falha:
            avisos.append({"codigo": "cache_usado", "mensagem": (
                f"A fonte {_origem(produto, f)} não respondeu; mostrando o cache obtido em {meta.get('obtido_em')}.")})

        versao = ({"valor": meta["versao"], "situacao": regras.CONFIRMADO_NO_ARQUIVO, "fonte": meta.get("versao_fonte")}
                  if meta.get("versao") else {"valor": None, "situacao": regras.DESCONHECIDO,
                                               "fonte": f"esperada {f['versao']} pela ficha; o cache não registrou"})
        if meta.get("versao") and meta["versao"] != f["versao"]:
            avisos.append({"codigo": "versao_diferente",
                           "mensagem": f"O cache é da versão {meta['versao']}; a ficha descreve a {f['versao']}."})
        unidade = ({"valor": f["unidade"], "situacao": regras.CONFIRMADO_NO_ARQUIVO, "fonte": f"atributo units = {meta['unidade_no_arquivo']}"}
                   if meta.get("unidade_no_arquivo") else {"valor": f["unidade"], "situacao": regras.DOCUMENTADO, "fonte": "ficha do produto"})
        aviso = regras.aviso_escala(f["resolucao_espacial"], f["resolucao_temporal"], cel["distancia_km"])
        base = _base(produto_meta, versao, cel, unidade, resolucao, aviso)

        if periodo_pedido is None:
            regra_periodo, novos, novos_avisos = _janela_validas(linhas, variante, variantes, f, base, janela_dias)
            itens += novos
            avisos += novos_avisos
            continue
        da_variante = sorted((r for r in linhas if r["variante"] == variante_usada), key=lambda r: r["chave"])
        a, b = periodo_pedido
        regra_periodo = {"valor": "dias_pedidos_sem_agregacao", "situacao": regras.HIPOTESE, "decisao": "D-008"}
        d = a
        while d <= b:
            do_dia = [r for r in da_variante if r["periodo_inicio"][:10] == d.isoformat()]
            if not do_dia:
                itens.append(_item_indisponivel(
                    "sem_registro: não há passagem/arquivo guardado para esta célula neste dia; nenhuma célula vizinha "
                    "ou estimativa é usada no lugar.", base,
                    {"inicio": d.isoformat(), "fim": d.isoformat(), "variante": variante_usada, "situacao": regras.DESCONHECIDO}))
            for r in do_dia:
                periodo = {"inicio": r["periodo_inicio"], "fim": r["periodo_fim"], "variante": variante_usada,
                           "granulo": r["granulo"], "situacao": regras.CONFIRMADO_NO_ARQUIVO}
                if r["situacao"] != "ok" or r["valor"] == "":
                    itens.append(_item_indisponivel(
                        "sem_dado_na_celula: o arquivo SMAP traz valor de preenchimento (sem recuperação) para esta "
                        "célula; nenhuma célula vizinha ou estimativa é usada no lugar.", base, periodo))
                    continue
                q = _qualidade(r, f)
                if q.get("recomendada") is False:
                    avisos.append({"codigo": "qualidade_nao_recomendada",
                                   "mensagem": f"O valor de {r['periodo_inicio'][:10]} não tem qualidade recomendada pela NASA."})
                itens.append(regras.item_contexto(estado="disponivel", valor=round(float(r["valor"]), 4), motivo=None,
                                                  periodo=periodo, qualidade=q, **base))
            d += dt.timedelta(days=1)

    if not pesos:
        regra_periodo = {"valor": None, "situacao": regras.DESCONHECIDO, "decisao": "D-008"}
    if any(i["estado"] == "indisponivel" for i in itens):
        avisos.append({"codigo": "celula_indisponivel", "mensagem": (
            "Há período ou célula sem dado SMAP. Ele aparece como indisponível, sem substituição.")})
    if sintetico:
        avisos.append({"codigo": "dado_sintetico", "mensagem": "Dados SINTÉTICOS de teste; não são observações da NASA."})

    resposta = {
        "natureza": regras.NATUREZA, "opcional": True, "uso": regras.USO,
        "local": local, "produto": produto_meta,
        "variante": {"valor": variante or (variantes if periodo_pedido is None else variante_usada),
                     "situacao": regras.DOCUMENTADO if variante else regras.HIPOTESE},
        "regra_periodo": regra_periodo, "decisoes_pendentes": [regras.DECISAO_PRODUTO],
        "celulas": celulas_saida, "itens": itens, "avisos": _unicos(avisos),
        "origem_dados": "+".join(sorted(origem_dados)) or None, "dado_sintetico": sintetico,
        "obtido_em": max(filter(None, obtido), default=None),
    }
    _garantir_contrato(resposta)
    return resposta


def _qualidade(r: dict, f: dict) -> dict:
    if f.get("regra_qualidade"):
        return regras.qualidade_l3(int(r["qualidade"]) if r["qualidade"] != "" else None, f.get("fill_qualidade"))
    return regras.qualidade_sem_flag(f["nivel"])


def _janela_validas(linhas: list[dict], variante: str | None, variantes: list[str], f: dict, base: dict,
                    janela_dias: int) -> tuple[dict, list[dict], list[dict]]:
    """Hipótese operacional do protótipo (#70): observações VÁLIDAS dos últimos `janela_dias` dias.

    O fim da janela é o último dia guardado no cache da célula, e não o relógio. Assim o mesmo cache
    sempre dá a mesma resposta. Válida = sem preenchimento e, quando o produto tem flag, bit 0 = 0
    (qualidade recomendada). Cada observação válida vira um item com a sua data. Nada é agregado.
    """
    usadas = [variante] if variante else variantes
    regs = sorted((r for r in linhas if r["variante"] in usadas), key=lambda r: (r["chave"], r["variante"]))
    regra = {"valor": "observacoes_validas_ultimos_dias", "janela_dias": janela_dias, "base_fim": "ultimo_dia_no_cache",
             "variantes": usadas, "situacao": regras.HIPOTESE,
             "origem": "hipótese operacional do protótipo proposta pelo usuário em resposta à #70; parametrizável",
             "decisao": "D-008"}
    if not regs:
        regra |= {"inicio": None, "fim": None, "contagem": None}
        return regra, [_item_indisponivel("sem_registro: o cache desta célula não tem as variantes pedidas.", base,
                                          {"inicio": None, "fim": None, "variante": ",".join(usadas)})], []
    fim = dt.date.fromisoformat(regs[-1]["periodo_inicio"][:10])
    inicio = fim - dt.timedelta(days=janela_dias - 1)
    na_janela = [r for r in regs if inicio.isoformat() <= r["periodo_inicio"][:10] <= fim.isoformat()]
    itens, sem_dado, nao_recomendada = [], 0, 0
    for r in na_janela:
        if r["situacao"] != "ok" or r["valor"] == "":
            sem_dado += 1
            continue
        q = _qualidade(r, f)
        if q.get("recomendada") is False:
            nao_recomendada += 1
            continue
        periodo = {"inicio": r["periodo_inicio"], "fim": r["periodo_fim"], "data": r["periodo_inicio"][:10],
                   "variante": r["variante"], "granulo": r["granulo"], "situacao": regras.CONFIRMADO_NO_ARQUIVO}
        itens.append(regras.item_contexto(estado="disponivel", valor=round(float(r["valor"]), 4), motivo=None,
                                          periodo=periodo, qualidade=q, **base))
    dias_com_registro = {r["periodo_inicio"][:10] for r in na_janela}
    contagem = {"observacoes_validas": len(itens), "registros_sem_dado": sem_dado,
                "registros_qualidade_nao_recomendada": nao_recomendada,
                "dias_sem_registro": janela_dias - len(dias_com_registro),
                "passagens_possiveis": janela_dias * len(usadas)}
    regra |= {"inicio": inicio.isoformat(), "fim": fim.isoformat(), "contagem": contagem}
    avisos = [{"codigo": "janela_hipotese", "mensagem": (
        f"Mostrando {len(itens)} observações válidas de {inicio.isoformat()} a {fim.isoformat()} "
        f"(janela de {janela_dias} dias, hipótese do protótipo). Cada valor traz a sua data.")}]
    if not itens:
        itens = [_item_indisponivel(
            f"sem_observacao_valida: nenhuma observação válida na janela de {janela_dias} dias; nenhuma célula "
            "vizinha ou estimativa é usada no lugar.", base,
            {"inicio": inicio.isoformat(), "fim": fim.isoformat(), "variante": ",".join(usadas), "situacao": regras.DESCONHECIDO})]
    return regra, itens, avisos


def _base(produto_meta, versao, celula, unidade, resolucao, aviso) -> dict:
    return {"produto": produto_meta, "versao": versao, "celula": celula, "unidade": unidade,
            "resolucao": resolucao, "aviso": aviso}


def _aneis(g: dict) -> list:
    return [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]


def _unicos(avisos: list[dict]) -> list[dict]:
    vistos, saida = set(), []
    for a in avisos:
        k = (a["codigo"], a["mensagem"])
        if k not in vistos:
            vistos.add(k)
            saida.append(a)
    return saida


def _garantir_contrato(resposta: dict) -> None:
    """Falha alto se a resposta violar o contrato de contexto regional (#53, #94, #95)."""
    erros = [f"item {i}: {e}" for i, it in enumerate(resposta["itens"]) for e in regras.validar_item(it)]
    erros += regras.termos_proibidos(resposta)
    erros += [f"chave proibida {k}" for k in regras.chaves(resposta) if k in regras.CHAVES_PROIBIDAS]
    if not resposta["itens"]:
        erros.append("resposta sem itens")
    if erros:
        raise AssertionError("contrato da umidade violado: " + "; ".join(erros))
