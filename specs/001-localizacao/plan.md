# Implementation Plan: Localização e referências do local

**Branch**: `001-localizacao` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-localizacao/spec.md`

## Summary

O usuário escolhe um ponto no Brasil (busca de município, coordenadas ou clique no mapa) e o
sistema devolve um **resultado de localização**: município/UF/código IBGE, célula POWER, célula
IMERG, estação INMET operante mais próxima, praça Conab mais próxima (no geral e por cultura),
cada item com fonte, data e distância, mais os avisos. Tudo é calculado com referências locais
versionadas (IBGE, INMET, Conab), em Python puro, sem rede na hora da consulta. Esta é a primeira
spec com código: ela cria o esqueleto do backend (FastAPI, uv) e do frontend (Astro + Tailwind)
que as próximas specs vão seguir.

## Technical Context

**Language/Version**: Python 3.12 ou superior (as máquinas do time têm 3.14.7); Node 24 ou
superior para o frontend

**Primary Dependencies**: FastAPI e Uvicorn (API); httpx (só no script de preparação e nos
testes); xlrd (só no script de preparação, para ler as abas da Conab); Astro, Tailwind CSS e
Leaflet (frontend)

**Storage**: arquivos JSON versionados em `referencias/localizacao/` (derivados, pequenos, com
procedência). As respostas brutas baixadas vão para `data/raw/localizacao/` (fora do Git, só com
`FONTE.md`)

**Testing**: pytest (regras e API); um teste de tela manual descrito em quickstart.md

**Target Platform**: máquina local da demo (Windows e Linux), navegador moderno

**Project Type**: aplicação web (backend de API e frontend estático)

**Performance Goals**: resolver um ponto em menos de 200 ms com as referências carregadas; busca
de município em menos de 100 ms; tudo isso para caber no SC-001 (escolher o local em menos de
30 s)

**Constraints**: offline depois da preparação (Princípio V); nenhuma constante sem fonte
(Princípio I); regras puras e determinísticas (Princípio IV); sem dependência geoespacial nativa
(GDAL/shapely)

**Scale/Scope**: 5.571 municípios, 668 estações, cerca de 40 praças; um usuário por vez (demo)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano cumpre | Situação |
|---|---|---|
| I. Todo número tem fonte | Cada referência leva `fonte`, `obtido_em` e `distancia_km`. O limite de 50 km fica em `limites.json` com `status: hipotese`. As praças são ligadas ao IBGE numa tabela versionada | ok |
| II. Honestidade | Avisos de estação distante, praça de outro município, divisa ambígua e lacunas, sem preencher nada em silêncio | ok |
| III. Chuva validada | Não se aplica diretamente. A 001 só aponta a célula IMERG e a estação; nada de chuva do POWER | ok |
| IV. Regras puras | `tellus.localizacao.regras` sem rede, sem relógio e sem estado global; teste de determinismo e caso Rio Verde | ok |
| V. Offline | As referências ficam no repositório e a consulta não usa rede. O mapa tem fundo offline | ok |
| VI. Escopo mínimo | Só ponto → referências. Talhão e várias lavouras ficam fora | ok |
| VII. Segredos | A 001 não usa credencial | ok |

Reavaliado depois da Fase 1: continua tudo ok, sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/001-localizacao/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── localizacao.openapi.yaml
└── tasks.md             # gerado por /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml            # uv; pacote "tellus"
├── src/tellus/
│   ├── __init__.py
│   ├── api/
│   │   ├── app.py            # FastAPI: cria a app, CORS para o frontend local
│   │   └── localizacao.py    # rotas /api/localizacao, /api/municipios
│   └── localizacao/
│       ├── regras.py         # puro: haversine, células POWER/IMERG, ponto-em-polígono, vizinho mais próximo
│       ├── referencias.py    # carrega os JSON de referencias/localizacao (somente leitura)
│       ├── busca.py          # normalização sem acento e busca parcial de municípios
│       └── servico.py        # monta o ResultadoLocalizacao a partir de regras e referências
└── tests/
    ├── localizacao/
    │   ├── test_regras.py        # células, haversine, ponto-em-polígono
    │   ├── test_rio_verde.py     # FR-015 / SC-002
    │   ├── test_capitais.py      # SC-003 (10 pontos)
    │   └── test_recusas.py       # fora do Brasil, coordenadas inválidas, oceano
    └── api/test_localizacao_api.py   # contrato

referencias/localizacao/      # versionado, gerado pelo script de preparação + correções manuais
├── FONTE.md
├── municipios.json           # código IBGE, nome, UF, centroide, bbox
├── malha_municipios.geojson  # malha IBGE qualidade mínima
├── brasil.geojson            # contorno do país
├── estacoes_inmet.json
├── pracas_conab.json         # praça → código IBGE, culturas e anos com planilha
└── limites.json              # 50 km (hipótese), 2 km de divisa

scripts/
└── preparar_localizacao.py   # baixa das fontes para data/raw/localizacao/ e gera referencias/localizacao/

frontend/
├── package.json              # Astro + Tailwind + Leaflet
├── astro.config.mjs
└── src/
    ├── pages/index.astro     # tela inicial com o seletor de local
    ├── components/
    │   ├── SeletorLocal.astro    # busca, coordenadas, mapa
    │   └── ReferenciasLocal.astro
    └── lib/api.ts            # cliente do contrato
```

**Structure Decision**: aplicação web com `backend/` e `frontend/` separados, porque as specs
seguintes (002 a 007) acrescentam módulos irmãos em `backend/src/tellus/` (`clima`, `zarc`,
`culturas`, `motor`, `economia`, `recomendacao`) e a 009 cresce dentro de `frontend/`. As
referências versionadas ficam em `referencias/<area>/`, um padrão que as specs 003, 004 e 006
também seguem. Um comando na raiz para iniciar tudo fica a cargo de `area:infra`; nesta spec,
o quickstart usa dois comandos.

## Complexity Tracking

Sem violações da constituição.
