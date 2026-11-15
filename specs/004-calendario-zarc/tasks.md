# Tasks: Calendário ZARC

Issues relacionadas: #40 (US-004), #41 (T-019), #60 (T-029), #61 (T-030), #62 (T-031), #63 (T-032), #64 (T-033).

## Phase 1: Setup

- [X] T001 Criar `backend/src/tellus/zarc/` e `referencias/zarc/culturas.json` com os códigos SISZARC das 4 culturas (research R2)

## Phase 2: Foundational

- [X] T002 [P] `backend/src/tellus/zarc/regras.py`: `decendio`, `periodo_decendio`, `codificar`/`decodificar`, `janela` (só risco ≠ 0) e `consultar`
- [X] T003 [P] `backend/tests/zarc/test_regras.py`: os 366 dias de 2028 caem no decêndio certo; bordas 10/11/20/21/31 e 29/02
- [X] T004 `backend/src/tellus/zarc/siszarc.py`: sessão que percorre os 8 combos, baixa o XLS por portaria × grupo (solo vazio = todos), grava o `.meta.json` com filtros, data e sha256, e lê o relatório por posição (defeito "Dev 35"), conferindo os rótulos

## Phase 3: US1 - Ver plantios permitidos (#40, #41, #60, #61)

- [X] T005 [US1] `scripts/preparar_zarc.py <UF...>`: baixa as 4 culturas, liga o nome do município ao IBGE (falha se algum ficar sem código) e grava `referencias/zarc/2026-2027/<UF>.json`
- [X] T006 [US1] `backend/src/tellus/zarc/servico.py`: `calendario` (grupos separados quando "não sei"; proveniência com portaria, data da portaria, safra, vigente e obtenção), `consultar_data` e `permitido`
- [X] T007 [US1] Rotas `/api/zarc/culturas`, `/api/zarc/calendario` e `/api/zarc/consulta`, com erro no formato padrão
- [X] T008 [US1] Rodar a preparação para GO (validação), MT e MS; MG, PR, BA, TO, MA, PI, SP e DF em andamento (entram em commit separado; UF não baixada responde `disponivel: false` com o comando para baixar)

## Phase 4: Bloqueio e separação de riscos (#62, #63)

- [X] T009 [US1] `permitido()` só devolve True com risco oficial ≠ 0; UF não baixada e combinação ausente dão `disponivel: false` sem inferência
- [X] T010 [US1] O campo `significado` e o nome `risco_zarc_pct` separam o risco ZARC do risco hídrico

## Phase 5: Validação (#64)

- [X] T011 `backend/tests/zarc/test_rio_verde.py`: milho G I (6 solos) e sorgo G I (3 solos) iguais ao REGISTRO; G II mais curto que G I; a referência é igual ao XLS salvo, linha a linha, para Rio Verde
- [X] T012 `backend/tests/zarc/test_servico.py`: "não sei" com 3 grupos separados, só decêndios com risco, dentro/fora, bloqueio, UF ausente, combinação ausente simulada e API
- [X] T013 Registrar no `REGISTRO.md` e no `MAPA_FEATURES.md`; comentar e fechar as issues #40, #41 e #60 a #64
