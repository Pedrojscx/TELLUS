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

## Nota de 2026-11-15: chuva ponderada por área (#35)

- `servico.serie(...)` e `resumo(...)` aceitam `geometria` + `id_geometria` (o mesmo id da confirmação da
  002/CAR, recalculado com `tellus.car.regras`). Rotas: `POST /api/clima/serie` e `POST /api/clima/resumo`.
  O `GET` por ponto não mudou.
- O peso de cada célula IMERG de 0,1° vem de `regras.pesos_celulas` (fração das amostras de 0,005° dentro
  do polígono; soma 1). A chuva diária vem de `regras.chuva_ponderada`: se uma célula com peso > 0 não tem
  valor, o dia inteiro fica `None`, com `celulas_sem_dado` e o aviso `dia_indisponivel_celula`. Nunca há
  renormalização nem zero.
- A proveniência (`localizacao.celulas[]`) traz, para cada célula, chave, centro, limites, peso, distância,
  origem, data de obtenção e qualidade (dias válidos, dias sem dado, contagem média). Também traz
  `soma_pesos`, `id_geometria`, `area_ha` e o método. O período inclui o fuso UTC.
- Cada fonte é carregada por célula: primeiro o cache local, depois a série versionada da MESMA célula. Se
  faltar qualquer célula, o resultado é o erro `sem_cache`, que nomeia a célula. O POWER usa a célula do
  centro do retângulo envolvente da área.
- Dado real: só a célula (−17,75; −50,95) tem série real. A geometria do CAR de teste cai em (−17,85; −51,05),
  sem cache: o pedido falha com `sem_cache`, nomeando a célula. Por decisão do usuário (2026-11-15), as células
  vizinhas não foram baixadas; o caso com várias células é provado só com cache sintético (`test_area.py`).
- Motor (spec 006): `_serie_com_eto` recebe `geometria`/`id_geometria`, e `preparar()` os repassa a partir do
  pedido. Sem geometria, nada muda (`tests/motor/test_geometria.py`).
