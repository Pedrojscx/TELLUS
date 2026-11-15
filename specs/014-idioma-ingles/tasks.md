# Tasks: Versão em inglês (site e sistema)

Issues relacionadas: #117 (US-014), #111 (T-077: T001–T002), #112 (T-078: T003–T004), #113 (T-079: T005), #114 (T-080: T006–T007), #115 (T-081: T008, T010), #116 (T-082: T009).

## Como ficou (15/11, 11h)

- O dicionário é `frontend/src/lib/i18n/en.ts`: a chave é a frase em português como aparece na tela. A marcação das telas não mudou. Com EN ativo, `cliente.ts` traduz a página e tudo o que as telas montam depois (MutationObserver), além de números e datas (`traduzir.ts`). Sem JavaScript ou em PT, nada muda.
- Backend (T005–T007): catálogo `backend/src/tellus/i18n/en.json` com frases exatas e modelos com campos nomeados (`{origem}`, `{data}`; `_lista` traduz cada item, `_t` traduz o campo). A chave é o texto em português, não o código: o mesmo código aparece com textos diferentes. A tradução acontece só na saída da API e só nos campos de texto (`CAMPOS_TEXTO`); números, códigos, estados e o `hash_pedido` não mudam.
- Contrato 1.2.0: campo opcional `idioma` no pedido; sem ele, vale o `Accept-Language`. As outras rotas usam o `Accept-Language` (middleware em `api/app.py`). O frontend manda os dois quando EN está ativo.
- Texto sem tradução sai com "(PT) ". `scripts/i18n_faltantes.py` lista o que falta: em 15/11, 53 de 383 textos do código, todos pedaços já cobertos por modelos ou textos internos (cabeçalhos da planilha Conab, listas de palavras proibidas, checagens de formato).
- Verificação (T008): ao vivo, o mesmo pedido de Rio Verde em PT e EN deu números e ordem idênticos e 0 "(PT)"; rotas de margem, solo e referências também. No navegador, o Resultado real em inglês ficou sem português visível. Testes: `backend/tests/i18n/test_idioma.py` e `frontend/src/lib/i18n/*.test.ts`.
- O tradutor do navegador continua como rede de segurança para textos fixos das telas.
- Limite conhecido: o botão de arquivo e o seletor de data são desenhados pelo navegador, no idioma do computador.

## Phase 1: Base de idioma no frontend (US1)

- [X] T001 `frontend/src/lib/i18n/` com `pt.ts`, `en.ts` e `idioma.ts` (idioma ativo: `?lang` > localStorage > `pt-BR`; função `t(chave, campos)`; formatação de número, moeda e data por idioma). Teste vitest: as chaves de `pt` e `en` são iguais (FR-002, FR-004, FR-008)
- [X] T002 Componente `SeletorIdioma.astro` (PT | EN em texto, atual marcado, acessível por teclado) no cabeçalho de `index.astro` e de `LayoutComparacao.astro`; `lang` do `<html>` em `Base.astro` acompanha o idioma; a troca mantém lavoura, entradas e premissas (FR-001, FR-003)

## Phase 2: Textos das telas (US1)

- [X] T003 Tela inicial e componentes do local (`SeletorLocal`, `ConsultaCar`, `ReferenciasLocal`, `DesenhoArea`, `EnvioArquivo`) com `t()`
- [X] T004 Comparação: `entradas`, `metodologia`, `premissas`, `resultado`, `carga`, `erros` e componentes de `components/comparacao/`, incluindo `etapas.ts`, `contrato.ts` (títulos, `textoAlteracao`, `produtos`) e `padroes.ts` (texto de proveniência)

## Phase 3: Mensagens do backend (US2)

- [X] T005 Catálogo `backend/src/tellus/i18n/` (`pt.json`, `en.json`: código → modelo com campos nomeados) e função `traduzir(codigo, idioma, **campos)` com fallback "(PT)"; os `_aviso`/`_erro` dos módulos (car, clima, contrato, localizacao, vegetacao, api) passam pelo catálogo (FR-006, FR-007)
- [X] T006 Contrato 1.2.0: campo opcional `idioma` no pedido, `Accept-Language` nas outras rotas, aceita pedidos 1.1.0; hipóteses, motivos de indisponibilidade e critério de ordem da recomendação também pelo catálogo; frontend envia o idioma ativo (FR-005)
- [X] T007 Testes: cobertura do catálogo (lista os códigos sem `en`); mesmo pedido em PT e EN com números e ordem idênticos (SC-003, SC-004, FR-009)

## Phase 4: Verificação e documentação (US2, US3)

- [X] T008 Teste do texto renderizado do resultado em inglês sem palavras portuguesas fora de uma lista de nomes próprios; palavras proibidas em inglês no guia de marca (SC-001, FR-010)
- [ ] T009 `README.en.md` linkado no topo do `README.md` (FR-011)
- [ ] T010 Roteiro manual em inglês no computador e no celular (caso de referência); registrar no registro da equipe e fechar as issues
