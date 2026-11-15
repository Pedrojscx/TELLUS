# Tasks: Economia

Issues relacionadas: #46 (US-007), #47 (T-022), #67 (T-036), #82 (T-051), #83 (T-052), #84 (T-053), #85 (T-054).

## Phase 1: Decisão e dados (#67)

- [X] T001 D-005: verificar a lista de indicadores do CEPEA (sem sorgo) e o portal de preços da Conab (certificado inválido); registrar a decisão na spec, no DUVIDAS e no research
- [X] T002 `scripts/preparar_economia.py`: ler as 65 planilhas Conab 2025/26 (itens, totais, mês, sistema, produtividade, divergências) e baixar a série CEPEA do milho para `referencias/economia/`

## Phase 2: Custo (#47, #82)

- [X] T003 `backend/src/tellus/economia/conab.py`: `ler_aba`, `conferir` (recomposição) e `custo_do_nivel` (itens incluídos e ajustes)
- [X] T004 `servico.praca_mais_proxima`: a praça mais próxima com a mesma cultura, com a distância e o ano mais recente

## Phase 3: Preço, edição e margem (#83, #84, #85)

- [X] T005 `servico.margem`:
  - preço CEPEA com metadados, sorgo indisponível e cobertura sem receita;
  - edições validadas com `alteracoes` e `comparacao` (margem anterior e nova);
  - cenários pelos percentis (D-006 provisória);
  - `margem_disponivel` falso quando falta dado obrigatório;
  - `versao_premissas`.
- [X] T006 Rotas `POST /api/economia/margem` (aceita a simulação da 006 direto) e `GET /api/economia/praca`
- [X] T007 `backend/tests/economia/test_economia.py`:
  - as 65 planilhas recompõem;
  - os itens somam o custo operacional;
  - praça e distância;
  - margem à mão;
  - metadados do CEPEA;
  - sorgo sem margem factual;
  - cobertura;
  - edição com antes e depois;
  - nível de custo;
  - edições inválidas;
  - versão;
  - API com simulação.
- [X] T008 Registrar no registro da equipe e no MAPA_FEATURES; comentar e fechar as issues após o merge
