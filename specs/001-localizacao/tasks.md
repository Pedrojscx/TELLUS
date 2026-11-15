# Tasks: Localização e referências do local

**Input**: Design documents from `/specs/001-localizacao/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/localizacao.openapi.yaml, quickstart.md

**Tests**: incluídos. A constituição exige casos de referência e determinismo (Princípio IV) e a spec
define os casos de conferência (FR-015, SC-002, SC-003, SC-005).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1, US2 ou US3 da spec

## Path Conventions

Backend em `backend/src/tellus/`, testes em `backend/tests/`, referências em
`referencias/localizacao/`, frontend em `frontend/src/` (veja plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: esqueleto que as specs 002 a 007 vão reaproveitar

- [ ] T001 Criar `backend/pyproject.toml` com uv (pacote `tellus`, layout `src/`, `requires-python = ">=3.12"`), dependências `fastapi` e `uvicorn` e grupo dev `pytest`, `httpx` e `xlrd`, com as versões conferidas na documentação oficial na hora de instalar; gerar o `backend/uv.lock`
- [ ] T002 [P] Criar os pacotes vazios `backend/src/tellus/__init__.py`, `backend/src/tellus/api/__init__.py` e `backend/src/tellus/localizacao/__init__.py`, e `backend/tests/conftest.py` com a fixture que aponta para `referencias/localizacao/` na raiz do repositório
- [ ] T003 [P] Criar o frontend Astro em `frontend/` com Tailwind CSS e Leaflet (`frontend/package.json`, `frontend/astro.config.mjs`, `frontend/src/pages/index.astro` vazio), conferindo na documentação oficial o comando atual de criação e de integração do Tailwind
- [ ] T004 [P] Acrescentar ao `.gitignore`: `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/` e `frontend/.astro/` (o `data/raw/**` já está coberto)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: referências locais e regras puras que todas as histórias usam

**⚠️ CRITICAL**: nenhuma história começa antes desta fase

- [ ] T005 Escrever `scripts/preparar_localizacao.py`. Ele baixa para `data/raw/localizacao/` (gravando um `.meta.json` com url, data e status HTTP de cada download):
  - a lista de municípios IBGE (`api/v1/localidades/municipios?view=nivelado`);
  - a malha municipal mínima (`api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio`);
  - o contorno do Brasil (mesma URL sem `intrarregiao`);
  - as estações INMET (`https://apitempo.inmet.gov.br/estacoes/T`, com User-Agent de navegador);
  - as três séries Conab: soja `.../agricolas/serie-historica-custos-soja-1997-a-2026.xls`, milho `.../agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls` (sem `/view`) e sorgo `.../agricolas/seriehistoricacustossorgo2013a2026.xls`.
- [ ] T006 No mesmo script, gerar `referencias/localizacao/municipios.json`. Cada item traz `codigo_ibge` ("exatamente 7 dígitos"), `nome`, `uf`, `centroide {lat, lon}` (calculado do polígono), `bbox [minLon, minLat, maxLon, maxLat]` e `nome_normalizado` ("minúsculas, sem acento"). Também copiar a malha para `referencias/localizacao/malha_municipios.geojson` e o contorno para `referencias/localizacao/brasil.geojson`, e informar qual município da lista (5.571) não tem polígono (5.570)
- [ ] T007 No mesmo script, gerar `referencias/localizacao/estacoes_inmet.json` com `codigo`, `nome`, `uf`, `lat`, `lon`, `altitude_m`, `situacao` ("Operante" ou "Pane") e `inicio_operacao`
- [ ] T008 No mesmo script, gerar `referencias/localizacao/pracas_conab.json` a partir dos nomes das abas "Município-UF-Ano" de 2025 e 2026: tirar o prefixo "OGM-", ligar cada praça ao código IBGE pelo nome normalizado mais UF, e aplicar a tabela manual de apelidos do próprio script ("P. do Leste" = Primavera do Leste-MT, "C. Novo do Parecis" = Campo Novo do Parecis-MT, "M. Cândido Rondon" = Marechal Cândido Rondon-PR, "S. Luiz Gonzaga" = São Luiz Gonzaga-RS). Cada praça traz `culturas {soja, milho_2a_safra, sorgo: [anos]}`. O script falha se alguma praça ficar sem código IBGE
- [ ] T009 Criar `referencias/localizacao/limites.json` com `estacao_distante_km: 50` (`status: "hipotese"`, motivo da spec) e `divisa_km: 2` (`status: "hipotese"`), e `referencias/localizacao/FONTE.md` com fonte, URL e data de cada arquivo; rodar o script e commitar as referências geradas
- [ ] T010 [P] Implementar `backend/src/tellus/localizacao/regras.py`, puro e sem I/O:
  - `haversine_km` com raio de 6371.0088;
  - `celula_power(lat, lon)` = (round(lat/0.5)·0.5, round(lon/0.625)·0.625);
  - `celula_imerg(lat, lon)` = (floor(lat/0.1)·0.1+0.05, floor(lon/0.1)·0.1+0.05), arredondado a 4 casas;
  - `ponto_em_poligono` (ray casting, com Polygon e MultiPolygon e buracos);
  - `mais_proximo(ponto, itens)` com desempate determinístico pelo identificador.
- [ ] T011 [P] Implementar `backend/src/tellus/localizacao/referencias.py`: carregar uma vez (cache em memória, somente leitura) os seis arquivos de `referencias/localizacao/`, expor `versao_referencias` (a data mais recente do FONTE/metadados) e montar a `Procedencia` (`fonte`, `url`, `obtido_em`, `status` em `fonte` ou `hipotese`) de cada tipo
- [ ] T012 [P] Testes de `regras.py` em `backend/tests/localizacao/test_regras.py`:
  - A025 (-17.785, -50.965) dá POWER (-18.0, -51.25) e IMERG (-17.75, -50.95);
  - o ponto antigo (-17.80, -50.92) dá POWER (-18.0, -50.625);
  - haversine entre a A025 e o centro IMERG fica a 4.23 ± 0.05 km;
  - ponto dentro e fora de um quadrado e de um polígono com buraco.
- [ ] T013 Criar `backend/src/tellus/api/app.py` com a app FastAPI, CORS liberado para `http://localhost:4321` (dev do Astro) e um handler que converte erros de domínio no formato `{erro: {codigo, mensagem, campo}}` do contrato

**Checkpoint**: referências commitadas, regras testadas, app sobe vazia

---

## Phase 3: User Story 1 - Escolher o local da lavoura (Priority: P1) 🎯 MVP

**Goal**: escolher o local por busca, coordenadas ou mapa, com Rio Verde-GO como padrão

**Independent Test**: buscar "rio verde" e ver Rio Verde-GO e Rio Verde de Mato Grosso-MS; escolher Rio Verde-GO e ver o código 5218805 e as coordenadas

### Tests for User Story 1

- [ ] T014 [P] [US1] Teste de contrato de `GET /api/municipios?busca=rio%20verde` em `backend/tests/api/test_localizacao_api.py`. Ele confere que vêm 5218805 (GO) e 5007406 (MS), que "goiania" sem acento acha Goiânia-GO e que `busca` com menos de 2 caracteres dá 422
- [ ] T015 [P] [US1] Teste em `backend/tests/localizacao/test_capitais.py`: as 10 capitais (Brasília, Goiânia, Cuiabá, Campo Grande, São Paulo, Belo Horizonte, Salvador, Manaus, Porto Alegre, Palmas, pelas coordenadas da sede) mais a A025 resolvem para o município certo (SC-003)

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implementar `backend/src/tellus/localizacao/busca.py`: normalizar o texto (sem acento, minúsculas, espaços colapsados) e ordenar primeiro quem começa com o texto, depois quem contém o texto, com empate por nome e UF; limite padrão 10, máximo 50
- [ ] T017 [US1] Em `backend/src/tellus/localizacao/servico.py`, implementar `municipio_do_ponto(lat, lon)`: filtro por bbox, depois ponto-em-polígono. Preencher `municipio_alternativo` quando outro polígono estiver a menos de `divisa_km`, e então aplicar o aviso `divisa_ambigua`
- [ ] T018 [US1] Implementar em `backend/src/tellus/api/localizacao.py` as rotas `GET /api/municipios`, `GET /api/localizacao/municipio/{codigo_ibge}` (ponto = centroide, `meio: "busca"`; 404 `municipio_nao_encontrado`) e `GET /api/localizacao/padrao` (Rio Verde-GO no ponto da A025, `meio: "padrao"`, `eh_demo: true`), e registrá-las em `app.py`
- [ ] T019 [P] [US1] Implementar `frontend/src/lib/api.ts`, o cliente tipado das quatro rotas do contrato, com a URL base configurável (`PUBLIC_API_URL`, padrão `http://localhost:8000`)
- [ ] T020 [US1] Criar `frontend/src/components/SeletorLocal.astro`:
  - campo de busca com sugestões, mostrando sempre "Nome-UF";
  - campos de latitude e longitude;
  - mapa Leaflet centralizado no Brasil, com o contorno de `brasil.geojson` (servido como estático) e tiles OSM quando houver rede;
  - o clique no mapa chama `/api/localizacao?meio=mapa`;
  - mostra o local confirmado (município, UF, código IBGE, coordenadas) e o selo "local da demonstração" quando `eh_demo` for verdadeiro.
- [ ] T021 [US1] Montar `frontend/src/pages/index.astro` com o `SeletorLocal`, carregar `/api/localizacao/padrao` ao abrir e aplicar o estilo base com Tailwind

**Checkpoint**: US1 funcional e testável sozinha (MVP)

---

## Phase 4: User Story 2 - Referências de dados e distâncias (Priority: P1)

**Goal**: as cinco referências com fonte, distância e avisos

**Independent Test**: Rio Verde-GO mostra A025, POWER (-18, -51.25), IMERG (-17.75, -50.95), a praça Rio Verde-GO e o município 5218805, todos com `procedencia`

### Tests for User Story 2

- [ ] T022 [P] [US2] Teste em `backend/tests/localizacao/test_rio_verde.py` (FR-015 / SC-002), com tolerância de 0.01° nas coordenadas:
  - estação A025 a 780.11 m e a menos de 0.1 km do ponto;
  - IMERG (-17.75, -50.95);
  - POWER (-18.0, -51.25);
  - praça "Rio Verde"-GO com soja, milho_2a_safra e sorgo de 2026;
  - `municipio_zarc` com o código 5218805;
  - toda referência com `procedencia.fonte`, `url` e `obtido_em`.
- [ ] T023 [P] [US2] Teste de avisos em `backend/tests/localizacao/test_avisos.py`:
  - um ponto no oeste do Amazonas (ex.: -6.5, -69.0) recebe `estacao_distante` se a estação mais próxima passar de 50 km;
  - Goiânia recebe `praca_outro_municipio` se a praça mais próxima não for Goiânia;
  - uma estação em "Pane" mais próxima que a operante aparece no aviso `estacao_em_pane_ignorada`.
- [ ] T024 [P] [US2] Teste de determinismo em `backend/tests/localizacao/test_determinismo.py`: o mesmo ponto resolvido duas vezes dá JSON idêntico (FR-013)

### Implementation for User Story 2

- [ ] T025 [US2] Em `backend/src/tellus/localizacao/servico.py`, implementar `resolver(lat, lon, meio)`, que devolve o `ResultadoLocalizacao` com as cinco referências na ordem fixa: celula_power, celula_imerg, estacao_inmet, praca_conab, municipio_zarc.
  - Cada referência traz `identificador`, `nome`, `lat`, `lon`, `distancia_km` (2 casas), `detalhes` conforme o data-model, `procedencia` e `avisos`.
  - O campo `avisos` do resultado é a união dos avisos das referências.
- [ ] T026 [US2] Em `servico.py`, implementar a praça Conab: a mais próxima no geral mais `mais_proxima_por_cultura` para soja, milho_2a_safra e sorgo, com nome e distância. Aplicar o aviso `praca_outro_municipio` quando o código IBGE da praça for diferente do município do ponto, e `referencia_inexistente` se não houver praça
- [ ] T027 [US2] Em `servico.py`, implementar a estação INMET: a operante mais próxima. Aplicar `estacao_distante` acima de `estacao_distante_km` e `estacao_em_pane_ignorada` quando uma estação em pane estiver mais perto
- [ ] T028 [US2] Fazer `GET /api/localizacao?lat&lon&meio` em `backend/src/tellus/api/localizacao.py` usar `resolver`, e as rotas `padrao` e `municipio/{codigo}` devolverem o resultado completo
- [ ] T029 [US2] Criar `frontend/src/components/ReferenciasLocal.astro`: uma lista com as cinco referências (tipo em linguagem simples, nome, distância em km, fonte com link e data), os avisos destacados no topo e, para a praça, as mais próximas por cultura. Incluir no `index.astro` abaixo do seletor

**Checkpoint**: US1 e US2 completas

---

## Phase 5: User Story 3 - Recusa fora do Brasil ou ponto inválido (Priority: P2)

**Goal**: mensagens claras e local anterior mantido

**Independent Test**: (40.71, -74.00) dá 422 `fora_do_brasil` e a tela mantém Rio Verde-GO

### Tests for User Story 3

- [ ] T030 [P] [US3] Teste em `backend/tests/localizacao/test_recusas.py`:
  - Nova York (40.71, -74.00) dá `fora_do_brasil`;
  - (95, 0) e lat "abc" dão `coordenada_invalida` com o `campo` certo;
  - um ponto no Atlântico perto da costa (ex.: -23.10, -42.50) dá `fora_de_municipio`;
  - Fernando de Noronha (-3.85, -32.42) resolve com o aviso `ilha_oceanica`.

### Implementation for User Story 3

- [ ] T031 [US3] Em `servico.py`, validar a faixa (-90..90 e -180..180) e o tipo. Fora do contorno de `brasil.geojson`, dar `fora_do_brasil`. Dentro do contorno mas sem município, dar `fora_de_municipio`. Para municípios insulares (código 2605459), aplicar o aviso `ilha_oceanica`. Mensagem padrão: "O TELLUS cobre apenas o território brasileiro"
- [ ] T032 [US3] No `SeletorLocal.astro`, mostrar o erro junto do campo ou do mapa e só trocar o local guardado quando a resposta vier sem erro

**Checkpoint**: todas as histórias funcionais

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T033 [P] Fundo offline do mapa: se os tiles falharem, mostrar só o contorno do Brasil e um aviso discreto "mapa sem fundo (sem internet)" em `frontend/src/components/SeletorLocal.astro`
- [ ] T034 [P] Medir o tempo de `resolver` (alvo de menos de 200 ms) e da busca (alvo de menos de 100 ms) num teste em `backend/tests/localizacao/test_desempenho.py`
- [ ] T035 Rodar o `quickstart.md` inteiro (passos 2 a 4), anotar o resultado e o cronômetro do SC-001 no `REGISTRO.md` e marcar a spec 001 como "implementada" em `docs/sdd/MAPA_SPECS.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (T001 a T004): sem dependências
- Foundational (T005 a T013): depende do Setup e bloqueia todas as histórias. T005 → T006 → T007 → T008 → T009 em sequência (mesmo script); T010, T011 e T012 em paralelo com o script
- US1 (T014 a T021): depende da Foundational
- US2 (T022 a T029): depende da Foundational. Usa `municipio_do_ponto` (T017), então começa depois de T017
- US3 (T030 a T032): depende de T017 e T025
- Polish: depois das histórias desejadas

### Within Each User Story

Testes primeiro (devem falhar), depois o serviço, a rota e a tela.

### Parallel Opportunities

- T002, T003 e T004 juntos
- T010, T011 e T012 enquanto o script de preparação roda
- Frontend (T019 a T021, T029) em paralelo com o backend, assim que o contrato estiver fixo
- Os testes [P] de cada história juntos

## Parallel Example: User Story 1

```text
T014 teste da busca na API   |  T015 teste das capitais  |  T016 busca.py  |  T019 api.ts
```

## Implementation Strategy

### MVP First (User Story 1 Only)

Setup, depois Foundational, depois US1: já dá para escolher o local e ver o município. Valide e
faça commit.

### Incremental Delivery

US2 traz as referências que as specs 002, 003 e 006 consomem, e vem logo depois do MVP. US3 por
último.

### Parallel Team Strategy

Uma pessoa no backend (T005 a T018 e T022 a T028) e outra no frontend (T003, T019 a T021 e T029),
combinando pelo contrato.

## Notes

- Toda constante nova vai para `referencias/localizacao/limites.json` com status (Princípio I).
- Commits pequenos por tarefa ou grupo; nada de `.env` (a 001 não usa credencial).
