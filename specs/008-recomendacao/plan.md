# Implementation Plan: Recomendação

**Branch**: `008-recomendacao` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

`POST /api/recomendacao` tem duas metodologias:
- **cultura_escolhida**: os decêndios permitidos de uma cultura;
- **calculo_completo**: culturas × grupos × decêndios.

As duas usam a mesma função, `avaliar_cultura`. Para cada grupo, ela pega os decêndios da janela
ZARC (004) por `simular_janela` (006). Em cada um, roda `motor.simular` (que versiona as entradas)
e `economia.margem` (007).

O cálculo completo é a avaliação de cada cultura juntada. Por isso a paridade (SC-001) vale por
construção e é testada. A recomendação só filtra e ordena:
- alternativas completas entram no ranking;
- as incompletas (sem preço, sem custo, decêndio antes da colheita) vão para `indisponiveis`, com
  o motivo.

## Technical Context

**Language/Version**: Python ≥ 3.12, módulo `tellus.recomendacao`

**Primary Dependencies**: nenhuma nova. A série de clima com ETo ganhou um cache em memória por
ponto (`lru_cache` em `motor._serie_com_eto`); o cálculo completo leva cerca de 1 s

**Testing**:
- paridade entre as metodologias;
- 100% das alternativas dentro da janela, conferidas pelo ZARC de novo;
- "não sei";
- sem recomendação quando falta dado;
- ordem declarada;
- API.

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | Cada alternativa traz a versão do motor e da economia, a portaria ZARC e as unidades | ok |
| II. Sem parâmetro inventado | Alternativa sem dado completo nunca é ranqueada; hipóteses listadas por alternativa | ok |
| III. Reprodutibilidade | Mesma entrada dá a mesma ordem; versões nas alternativas | ok |
| IV. Escala / não previsão | Avisos `nao_e_previsao` e `riscos_distintos` | ok |
| V. Premissas | `edicoes_cultura` e `edicoes_economia` por cultura, mais `percentis` | ok |
| VI. Puro | A ordenação é pura sobre os resultados; o motor não é reimplementado | ok |

## Project Structure

```text
backend/src/tellus/recomendacao/servico.py
backend/src/tellus/api/recomendacao.py     # POST /api/recomendacao
backend/tests/recomendacao/test_recomendacao.py
```

## Complexity Tracking

Sem violações.
