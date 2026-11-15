# Tasks: Recomendação

Issues relacionadas: #48 (US-008), #108 (US-008.2), #49 (T-023), #68 (T-037), #86 (T-055), #87 (T-056), #88 (T-057), #89 (T-058), #90 (T-059).

## Phase 1: Decisão (#68)

- [X] T001 D-006: quartis da perda (P75/P50/P25), decisão de produto declarada e editável; registrar na spec, no DUVIDAS e no research

## Phase 2: Avaliação compartilhada (#49, #86, #87, #89)

- [X] T002 `avaliar_cultura`:
  - grupos do ZARC ("não sei" = todos);
  - decêndios da janela pelo motor (`simular_janela`);
  - em cada decêndio, `motor.simular` (versões) e `economia.margem`;
  - risco ZARC, risco histórico e margem em campos separados;
  - versões, unidades e hipóteses;
  - incompletos vão para `indisponiveis`.
- [X] T003 Cache em memória da série com ETo por ponto (`motor._serie_com_eto`)

## Phase 3: US1 e US2 (#48, #108, #88, #90)

- [X] T004 `ordenar` com o critério público e `recomendar` com as duas metodologias; `sem_recomendacao` quando não há alternativa completa
- [X] T005 Rota `POST /api/recomendacao`
- [X] T006 `backend/tests/recomendacao/test_recomendacao.py`:
  - paridade;
  - ZARC em 100%;
  - "não sei" com 3 grupos de sorgo;
  - ordem;
  - campos separados e avisos;
  - sem dados não recomenda;
  - completo sem edições só ranqueia o milho;
  - grupo informado;
  - erros;
  - API.
- [X] T007 Registrar no REGISTRO e no MAPA_FEATURES; comentar e fechar as issues após o merge
