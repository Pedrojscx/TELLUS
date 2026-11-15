# Implementation Plan: Calendário ZARC

**Branch**: `004-calendario-zarc` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

Para o município da lavoura (código IBGE da 002), o sistema devolve a janela oficial do ZARC
(safra 2026/2027, sequeiro) de milho 2ª safra, sorgo granífero 2ª safra, milho 2ª safra com
braquiária (referência da cobertura) e soja:
- a janela vem por grupo de cultivar e por solo, só com os decêndios de risco diferente de zero;
- cada grupo traz portaria, data da portaria, safra, se o conjunto é vigente e a data de obtenção.

Também responde a consulta de uma data de semeadura e expõe `permitido()`, que a recomendação
(008) usa para bloquear plantio fora da janela. Os relatórios vêm do SISZARC sem login, um XLS
por UF × cultura × portaria × grupo, e viram `referencias/zarc/<safra>/<UF>.json`.

## Technical Context

**Language/Version**: Python ≥ 3.12, pacote `tellus` (módulo `tellus.zarc`)

**Primary Dependencies**: httpx (formulário SISZARC); xlrd (relatório XLS, já usado na 002)

**Storage**:
- XLS brutos em `data/raw/zarc/siszarc/`, com `.meta.json` (filtros, data e sha256), fora do Git;
- referência derivada por UF em `referencias/zarc/2026-2027/<UF>.json`. Os riscos ficam
  codificados em 36 caracteres (`0`, `2`, `3`, `4`) por município × cultura × grupo × solo.

**Testing**: pytest. Rio Verde é conferido contra os valores do REGISTRO e contra o XLS salvo
(quando presente)

**Performance Goals**: consulta em menos de 50 ms com a UF carregada; uma UF nova (4 culturas)
leva cerca de 1 a 5 min de download

**Constraints**:
- nunca inferir janela de vizinho;
- "não sei" o grupo devolve todos os grupos separados;
- risco ZARC e risco hídrico nunca se misturam.

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | Cada grupo traz fonte, portaria, data da portaria, safra, vigente, data de obtenção, url e sha256 do XLS | ok |
| II. Sem parâmetro inventado | Os riscos são da portaria. O rótulo dos solos tipo 1/2/3 é só descritivo | ok |
| III. Reprodutibilidade | O XLS é recriado por `scripts/preparar_zarc.py`, com hash. A referência é determinística | ok |
| IV. Escala | O ZARC é municipal; a resposta diz isso no `significado` | ok |
| VI. Puro | `tellus.zarc.regras` (decêndio, janela, codificação) é puro, testado em todos os dias de um ano bissexto | ok |
| VII. Degradação | UF não baixada ou combinação ausente: `disponivel: false` com o motivo, sem inferência | ok |
| VIII/IX | Sem credencial; branch própria | ok |

## Project Structure

```text
backend/src/tellus/zarc/{regras.py, siszarc.py, servico.py}
backend/src/tellus/api/zarc.py                      # /api/zarc/{culturas,calendario,consulta}
backend/tests/zarc/{test_regras.py, test_rio_verde.py, test_servico.py}
referencias/zarc/culturas.json                      # códigos SISZARC das 4 culturas
referencias/zarc/2026-2027/<UF>.json
scripts/preparar_zarc.py
```

## Complexity Tracking

Sem violações.
