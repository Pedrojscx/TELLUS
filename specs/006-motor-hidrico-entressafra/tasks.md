# Tasks: Motor hídrico e entressafra

Issues relacionadas: #44 (US-006), #45 (T-021), #66 (T-035), #78 (T-047), #79 (T-048), #80 (T-049), #81 (T-050).

## Phase 1: Decisão (#66)

- [X] T001 D-004: estado inicial, entressafra (pousio e palhada) e intervalo como hipóteses editáveis em `referencias/motor/premissas.json`; registrar na spec, no DUVIDAS e no research
- [X] T002 Acrescentar `p_esgotamento` (FAO-56, Tab. 22, hipótese) e o limite de ISNA da braquiária (hipótese) em `referencias/culturas/parametros.json`, mais o domínio da edição em `tellus.culturas.servico`

## Phase 2: Motor puro (#45)

- [X] T003 [P] `backend/src/tellus/motor/eto.py`: Penman-Monteith FAO-56 (eq. 6, 11, 19, 21) com intermediários
- [X] T004 [P] `backend/src/tellus/motor/balanco.py`: curva de Kc, passo diário (Ks, ETa, drenagem, limite de murcha), entressafra, safra (ISNA e déficit por fase, perda FAO-33, falha severa)
- [X] T005 `backend/src/tellus/motor/simulacao.py`: anos da série com a mesma colheita e o mesmo plantio, exclusão por dia ausente, risco histórico, déficit mediano e quantis de perda
- [X] T006 [P] `backend/tests/motor/test_eto.py` (Exemplo 18 da FAO-56) e `test_balanco.py` (caso à mão de 4 dias, drenagem, dia ausente, pousio × palhada, determinismo)

## Phase 3: US1 - Comparar água por alternativa (#44, #78, #79, #80, #81)

- [X] T007 [US1] `backend/src/tellus/motor/servico.py`:
  - `preparar`: localização, premissas, solo, entressafra e estado inicial;
  - `_checar_zarc`: rejeita fora da janela, com a portaria;
  - `simular`: entradas com hash, `versao_entradas`, avisos de hipótese e de não previsão;
  - `simular_janela`: risco por decêndio da janela.
- [X] T008 [US1] Rotas `POST /api/motor/simular` e `POST /api/motor/janela`
- [X] T009 [US1] `backend/tests/motor/test_servico.py`:
  - socket bloqueado e determinismo;
  - versões das entradas;
  - fora da janela e bordas do decêndio 5/6;
  - risco crescente;
  - aviso de não previsão;
  - pousio × palhada;
  - API.
- [X] T010 Registrar no REGISTRO e no MAPA_FEATURES; comentar e fechar as issues após o merge
