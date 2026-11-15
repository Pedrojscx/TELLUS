# Implementation Plan: Motor hídrico e entressafra

**Branch**: `006-motor-hidrico-entressafra` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

O motor é um balanço hídrico diário da FAO-56 (Kc único, reservatório da zona radicular com CAD
da portaria ZARC), com a ETo calculada por Penman-Monteith a partir do POWER e a chuva do IMERG.
Cada ano da série é uma simulação com a mesma data de colheita da soja e de plantio:
1. **Entressafra explícita**: da colheita até a véspera do plantio, com pousio ou palhada.
2. **Ciclo da cultura**: as fases vêm da portaria (ou de hipótese).

Por ano, ele devolve o ISNA por fase, o déficit, a perda relativa (FAO-33 multiplicativa, quando
há Ky) e a falha severa (ISNA da fase I ou III abaixo do limite da portaria). Com os anos juntos,
devolve o risco histórico, o déficit mediano e os quantis de perda. Só calcula dentro da janela
ZARC. Todas as entradas saem versionadas com hash. O cálculo (`eto`, `balanco`, `simulacao`) é
puro; o `servico` só junta as entradas das specs 003, 004 e 005.

## Technical Context

**Language/Version**: Python ≥ 3.12, módulo `tellus.motor`

**Primary Dependencies**: nenhuma nova

**Storage**: `referencias/motor/premissas.json` (estado inicial, Kc da entressafra, intervalo
de plantio, todos hipótese). O `p` (FAO-56, Tab. 22) foi acrescentado como hipótese em
`referencias/culturas/parametros.json`

**Testing**: pytest. ETo contra o Exemplo 18 da FAO-56; caso do balanço à mão; teste com a rede
bloqueada (socket bloqueado); bordas da janela ZARC

**Performance Goals**: uma simulação de 25 anos em menos de 0,5 s; a janela inteira (até 9
decêndios) em menos de 3 s

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | `entradas` traz clima (proveniência 003), solo (passos 005), cultura (parâmetros e alterações), estado inicial, entressafra e regra ZARC, cada um com hash; mais `versao_entradas` | ok |
| II. Sem parâmetro inventado | p, Kc, Ky, estado inicial e entressafra são hipótese (motivo) e aparecem no aviso `hipoteses` | ok |
| III. Reprodutibilidade | Mesmas entradas dão o mesmo resultado (teste); os hashes permitem reproduzir | ok |
| IV. Escala / não previsão | Aviso `nao_e_previsao` e `escala_regional`; "risco histórico" nunca é chamado de previsão | ok |
| V. Premissas editáveis | `edicoes` (005), `armazenamento_inicial_frac`, `entressafra.kc` e `data_plantio` | ok |
| VI. Motor puro | `eto`, `balanco` e `simulacao` sem rede, relógio ou estado; caso à mão e FAO Ex. 18; teste com socket bloqueado | ok |
| VII. Degradação | Dia climático ausente exclui o ano com motivo; ZARC indisponível dá 409 com o motivo | ok |

## Project Structure

```text
backend/src/tellus/motor/{eto.py, balanco.py, simulacao.py, servico.py}
backend/src/tellus/api/motor.py          # POST /api/motor/simular, POST /api/motor/janela
backend/tests/motor/{test_eto.py, test_balanco.py, test_servico.py}
referencias/motor/premissas.json
```

## Complexity Tracking

Sem violações.
