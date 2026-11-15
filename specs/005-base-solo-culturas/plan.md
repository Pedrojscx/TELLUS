# Implementation Plan: Base de solo e culturas

**Branch**: `005-base-solo-culturas` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

A base fica num arquivo versionado (`referencias/culturas/parametros.json`) com os parâmetros que
o motor hídrico (006) consome para milho 2ª safra, sorgo granífero 2ª safra e braquiária de
cobertura: profundidade efetiva de raiz, CAD por classe de solo, fases, limites de ISNA, Kc e Ky.
- **Com fonte**: o que está na portaria ZARC (raiz, CAD, fases do milho, ISNA), com validade
  regional (UF e safra).
- **Hipótese**: Kc e Ky (FAO-56/33 só como método de referência, nunca como fonte), as fases do
  sorgo (a portaria não publica) e toda a braquiária (não há ZARC para ela).

O solo se classifica pela equação oficial da IN 1/2022 (granulometria), pela textura (oficial no
sorgo, hipótese nas culturas AD) ou pela CAD informada pelo produtor. As edições preservam o
padrão, mostram antes e depois e respeitam o domínio físico.

## Technical Context

**Language/Version**: Python ≥ 3.12, módulo `tellus.culturas`

**Primary Dependencies**: nenhuma nova

**Storage**: `referencias/culturas/parametros.json` (versionado). Os PDFs das portarias e da IN
foram lidos em 15/11; os trechos citados ficam em cada parâmetro (`trecho`)

**Testing**: pytest, com caso à mão da equação e auditoria de fonte ou hipótese em todos os
parâmetros

**Constraints**:
- a FAO nunca aparece como `fonte`;
- uma fonte fora da validade regional vira hipótese com motivo;
- uma edição fora do domínio dá erro, sem ajuste silencioso.

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | Cada parâmetro traz documento, trecho, url, data de consulta e validade regional | ok |
| II. Sem parâmetro inventado | Sem fonte, `status: hipotese` com motivo. Teste de auditoria; teste de que a FAO nunca é fonte | ok |
| III. Reprodutibilidade | Arquivo versionado e funções puras | ok |
| IV. Escala | A validade regional da portaria (UF) é aplicada; fora dela, hipótese | ok |
| V. Premissas editáveis | `premissas()` com edições, `alteracoes` com antes e depois, domínio validado | ok |
| VI. Puro | `solo.py` (equação e classes) é puro, com caso à mão documentado no teste | ok |
| VII–IX | Sem rede e sem credencial; branch própria | ok |

## Project Structure

```text
backend/src/tellus/culturas/{solo.py, servico.py}
backend/src/tellus/api/culturas.py   # /api/culturas, /api/culturas/{c}/parametros, /api/culturas/premissas, /api/solo/classificar
backend/tests/culturas/{test_solo.py, test_premissas.py}
referencias/culturas/parametros.json
```

## Complexity Tracking

Sem violações.
