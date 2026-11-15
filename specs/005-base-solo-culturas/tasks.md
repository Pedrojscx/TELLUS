# Tasks: Base de solo e culturas

Issues relacionadas: #42 (US-005), #43 (T-020), #65 (T-034), #74 (T-043), #75 (T-044), #76 (T-045), #77 (T-046).

## Phase 1: Pesquisa (#65)

- [X] T001 Ler a IN SPA/MAPA nº 1/2022 (classes e equação) e as portarias 322 (milho) e 273 (sorgo) de GO; registrar em `research.md` e responder a D-003 no `DUVIDAS_ETAPA1.md`

## Phase 2: Base (#43, #77)

- [X] T002 `referencias/culturas/parametros.json`: parâmetros de milho, sorgo e braquiária com `fonte` (documento, trecho, url, data, validade regional) ou `hipotese` (motivo), e a FAO-56/33 em `metodos_referencia`
- [X] T003 [P] `backend/src/tellus/culturas/solo.py`: equação do Art. 3º e classes do Art. 2º (puro)
- [X] T004 [P] `backend/tests/culturas/test_solo.py`: caso à mão 60/15/25 → 0,909 mm/cm; limites das classes; classes × 60 cm = CAD da Port. 322; granulometria inválida

## Phase 3: US1 - Informar e conferir solo (#42, #74, #75, #76)

- [X] T005 [US1] `backend/src/tellus/culturas/servico.py`:
  - `parametros(cultura, uf)`, que vira hipótese fora da validade regional;
  - `premissas(cultura, uf, edicoes)`, que preserva o padrão, valida o domínio e devolve `alteracoes`;
  - `classificar_solo`: granulometria (oficial), textura (oficial no sorgo, hipótese nas culturas AD), classe ou CAD do produtor; passos com status.
- [X] T006 [US1] Rotas `/api/culturas`, `/api/culturas/{cultura}/parametros`, `/api/culturas/premissas` e `/api/solo/classificar`
- [X] T007 [US1] `backend/tests/culturas/test_premissas.py`:
  - auditoria de fonte completa ou hipótese em todas as culturas;
  - a FAO nunca é fonte;
  - validade regional;
  - edição com antes e depois e padrão preservado;
  - edições inválidas;
  - solo por granulometria, textura, tipo do sorgo e CAD;
  - API.
- [X] T008 Registrar no registro da equipe e no MAPA_FEATURES (feito); comentar e fechar (após o merge) as issues #42, #43, #65 e #74 a #77
