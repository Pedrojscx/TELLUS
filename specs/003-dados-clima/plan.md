# Implementation Plan: Dados de clima

**Branch**: `003-dados-clima` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-dados-clima/spec.md`

## Summary

Para um local (ponto da 002, entrega 1, ou polígono quando a 002 entregar), o sistema monta a
série diária usada pelo motor hídrico (006):
- chuva do IMERG Final V07B, com média ponderada pelas células de 0,1°;
- Tmax, Tmin, radiação, umidade e vento do NASA POWER;

cada série com os seis itens de proveniência do Princípio I. À parte, entrega a validação local
contra a estação INMET (A025 em Rio Verde-GO), que deve reproduzir viés de -1,03% e MAE de
4,13 mm/dia em 1.218 dias. O cache é por célula e por ponto, retomável. Rio Verde-GO vem
exportado em `referencias/` para a demo rodar sem rede.

## Technical Context

**Language/Version**: Python ≥ 3.12 (o mesmo pacote `tellus` da entrega 1 da 002)

**Primary Dependencies**: FastAPI e httpx (já existiam); h5py 3.16 (lê a resposta DAP4 `.nc4`)

**Storage**: cache CSV/JSON em `data/raw/clima/` (fora do Git); exportação derivada de Rio Verde em
`referencias/clima/rio_verde_go/` (versionada)

**Testing**: pytest com a rede bloqueada nos testes de regras e serviço; os clientes são testados
com respostas gravadas

**Target Platform**: máquina local da demo

**Project Type**: aplicação web (módulo novo `tellus.clima` + rotas)

**Performance Goals**: série de Rio Verde (cerca de 9 mil dias) em menos de 1 s a partir do
cache; local novo em menos de 25 min na primeira vez (download do IMERG)

**Constraints**: chuva do POWER nunca vai para a série de cálculo; dia ausente nunca vira zero;
o token só vem de variável de ambiente

**Scale/Scope**: 2001-01-01 até o último dia publicado do IMERG (hoje 2025-09-30)

## Constitution Check

| Princípio | Como o plano cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | Cada série traz `proveniencia` com fonte, versão, período, unidade, localização e qualidade. Um teste percorre a resposta | ok |
| II. Sem parâmetro inventado | Não há parâmetro agronômico. Os limiares (contagem mínima e cobertura) ficam em `referencias/clima/limites.json` com status | ok |
| III. Reprodutibilidade | Mesmo pedido com o mesmo cache dá resposta idêntica (teste). O bruto é recriado por `scripts/baixar_imerg.py` e `scripts/baixar_power.py`, com hash no `FONTE.md` | ok |
| IV. Respeito à escala | A resposta mostra resolução (0,1° diário; 0,5°×0,625° diário) e o aviso de escala; nada de "previsão" | ok |
| V. Premissas editáveis | Não se aplica: não há premissa nesta spec | n/a |
| VI. Motor puro | `tellus.clima.regras` (pesos, média ponderada, métricas) é puro e roda com a rede bloqueada; o caso à mão é a média ponderada de 2 células em 3 dias | ok |
| VII. Degradação explícita | Sem rede: usa o cache e avisa a data; sem cache: erro com código, mensagem e fonte | ok |
| VIII. Segredos | Token só por `EARTHDATA_TOKEN`; o script lê o `.env` para o ambiente sem exibir. Nenhum log ou resposta contém o token (teste) | ok |
| IX. Stack e trabalho | Python/uv, branch própria, commits em PT-BR | ok |
| Decisões de dados | IMERG é a chuva; INMET valida; chuva POWER só na comparação | ok |

Reavaliado depois do design: sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/003-dados-clima/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/clima.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/src/tellus/clima/
├── __init__.py
├── imerg.py        # cliente DAP4 + cache por célula (rede)
├── power.py        # cliente POWER + cache por ponto (rede)
├── regras.py       # puro: pesos de células, média ponderada, métricas de validação
├── referencias.py  # lê limites e a exportação de Rio Verde; localiza o cache
└── servico.py      # monta SerieClimatica, Validacao e Resumo com proveniência
backend/src/tellus/api/clima.py     # rotas /api/clima/*
backend/tests/clima/                # regras, serviço, rastreabilidade, segredo, Rio Verde
scripts/baixar_imerg.py  scripts/baixar_power.py  scripts/exportar_clima_rio_verde.py
referencias/clima/limites.json
referencias/clima/rio_verde_go/{serie_diaria.csv, FONTE.md}
```

**Structure Decision**: segue a estrutura da entrega 1 da 002 (`tellus/<area>/`,
`referencias/<area>/`). A interface (tela de fontes) fica para a 012; aqui entram só as rotas.

## Complexity Tracking

Sem violações.
