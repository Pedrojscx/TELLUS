# Tasks: Identidade visual

Issues relacionadas: #58 (US-013), #59 (T-028), #73 (T-042), #105 (T-074), #106 (T-075), #107 (T-076).

## Phase 1: Decisão (#73)

- [X] T001 Três paletas candidatas com contraste AA calculado (≥ 4,5:1 em todos os papéis); escolha do LK: paleta "Safra" e tom técnico e direto; D-011 registrada na spec e no DUVIDAS

## Phase 2: Guia e elementos (#105)

- [X] T002 `docs/marca/GUIA_DE_MARCA.md`: nome, ícone, cores, estados, tom com exemplos e palavras proibidas, tipografia e inventário de licenças
- [X] T003 Ícone próprio (`frontend/public/favicon.svg` = `docs/marca/tellus-icone.svg`); remover o favicon padrão do Astro (elemento de terceiros)

## Phase 3: Contraste e sinais textuais (#106)

- [X] T004 `frontend/src/styles/marca.css`: tokens do Tailwind 4 (`--color-tellus-*`) e a classe `.tellus-selo` com traço por estado (o tracejado distingue a hipótese em monocromia)
- [X] T005 `frontend/src/components/marca/Selo.astro`: texto obrigatório + ícone SVG próprio por estado; `role="alert"` no erro
- [X] T006 `scripts/verificar_contraste.py` (lê o `marca.css`, 20 pares, sai com erro abaixo de 4,5:1) e `backend/tests/marca/test_marca.py`

## Phase 4: Aplicação depois do fluxo funcional (#59, #107), bloqueada pela 012 (#56)

- [X] T007 Com a `012-interface-web` na `main`: importar `marca.css` no `global.css` e usar `Selo.astro` nos estados das telas
- [X] T008 Comparar as telas principais antes e depois: fonte, hipótese, aviso e erro visíveis; nenhum texto de previsão; registrar no registro da equipe
- [X] T009 Fechar #59, #107 e #58
