# Tasks: Contrato de API (011)

**Input**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Tests**: obrigatórios (pedido do Maestro e SC-001/SC-002).
**Issues**: #54 (US-011) · #55 versão · #96 pedido · #97 resposta · #98 resultado/aviso/erro · #99 contextos · #71 D-009 (pendente)
**Formato**: `- [ ] Txxx [P?] [US1] descrição com caminho`. A spec tem uma única história (US1), dividida por issue.

## Phase 1: Setup

- [X] T001 Criar o pacote `backend/src/tellus/contrato/__init__.py` e a pasta `backend/tests/contrato/`
- [X] T002 [P] Criar `backend/src/tellus/contrato/limites.json` (D-009): `max_vertices_anel` lido de `referencias/car/limites.json` (status `hipotese`); `tamanho_max_arquivo_bytes`, `prazo_processamento_s` e `area_max_ha` com `valor: null`, `status: "decisao_pendente"`, `decisao: "D-009"`, `issue: "#71"`

## Phase 2: Foundational

- [X] T003 Implementar `backend/src/tellus/contrato/versao.py` (#55): `VERSAO = "1.0.0"`, `compativel(v)` (mesmo MAIOR, MENOR ≤ servidor), `versoes_aceitas()`, `ErroContrato(codigo, mensagem, origem, campo, status, versoes_aceitas)`
- [X] T004 Implementar os modelos pydantic em `backend/src/tellus/contrato/modelos.py`, como no data-model.md:
  - `Proveniencia`: fonte, versao, periodo, unidade, localizacao e qualidade, todos "str não vazios", mais `cobre`;
  - `Aviso` (`tipo="aviso"`), `ErroFonte` (`tipo="erro"`, código, mensagem PT-BR, origem, cache, ação), `EstadoFonte`, `Secao` e `ContextoOpcional`;
  - `PedidoCalculo`, com "solo: exatamente um entre textura, cad_mm, classe, granulometria", "cultura obrigatória só em cultura_escolhida" e "`confirmada` precisa ser true";
  - `RespostaCalculo`.
- [X] T005 Implementar as regras puras em `backend/src/tellus/contrato/regras.py`:
  - `hash_estavel`;
  - `numeros_sem_proveniencia(resposta)`, que percorre `secoes.*.conteudo` e exige cobertura por um padrão de proveniência completa;
  - `estado_geral(secoes, fontes)`;
  - `validar_geometria(geom)`, que reusa `tellus.car.regras.validar_poligono` com o limite da T002.

## Phase 3: User Story 1 — Receber resultado rastreável (P1) 🎯 MVP

**Goal**: a interface recebe um resultado completo e versionado e entende o que é resultado, aviso e erro.
**Independent Test**: um pedido válido e uma resposta gravada passam na validação da versão (SC-001), e todo número da resposta tem proveniência completa (SC-002).

### Tests (escrever antes, devem falhar)

- [X] T006 [P] [US1] `backend/tests/contrato/test_versao.py` (#55): versão atual aceita; MENOR maior e MAIOR diferente → `versao_incompativel` com `versoes_aceitas`; pedido e resposta carregam a versão
- [X] T007 [P] [US1] `backend/tests/contrato/test_pedido.py` (#96): pedido completo válido; cada campo obrigatório ausente; solo com dois modos; área não confirmada; geometria inválida (anel aberto, autointerseção, acima do limite de vértices) → erro claro e o cálculo não inicia; premissa editada preserva `valor_padrao`
- [X] T008 [P] [US1] `backend/tests/contrato/test_resposta.py` (#97): a resposta montada com as saídas reais da 006/007 (Rio Verde, offline) valida no modelo; `numeros_sem_proveniencia == []`; um número sem cobertura é acusado; versões de entradas e contrato presentes; a seção 008 fica `pendente`, sem campos de ranking
- [X] T009 [P] [US1] `backend/tests/contrato/test_fontes.py` (#98): sucesso → `final`; cache → `final_com_cache` com aviso e data; falha sem cache → `erro`, `final=false`, erro com código, mensagem PT-BR e origem; estruturas `tipo` distintas
- [X] T010 [P] [US1] `backend/tests/contrato/test_contextos.py` (#99): valida com e sem cada contexto e com contexto em erro; `hash_principal` e `estado_geral` iguais; os avisos do contexto ficam no contexto
- [X] T011 [P] [US1] `backend/tests/contrato/test_exemplos.py` (SC-001): todos os `contracts/exemplos/*.json` passam (os válidos) ou falham com o código esperado (os de erro); os esquemas gravados são iguais aos gerados; determinismo
- [X] T012 [P] [US1] `backend/tests/contrato/test_api.py`: `GET /api/contrato/versao` com limites e status D-009; `GET /api/contrato/esquema`; `POST /api/contrato/pedido/validar` (200 normalizado; 422 versão, geometria e campo, no envelope `{erro:{codigo,mensagem,origem,campo}}`)

### Implementation

- [X] T013 [US1] Adaptadores em `backend/src/tellus/contrato/secoes.py`:
  - `secao_risco_hidrico(saida_006)`: proveniência de `entradas.clima.proveniencia`, solo, cultura e zarc;
  - `secao_economia(saida_007)`: proveniência de `custo_conab.fonte`, `premissas.preco.fonte`, produtividade Conab e percentis D-006;
  - `secao_recomendacao_pendente()`;
  - `contexto(id, resposta_modulo | erro | None)`;
  - `montar_resposta(pedido, secoes, contextos, fontes)`, com o hash principal sem os contextos.
- [X] T014 [US1] `normalizar_pedido(dict)` em `backend/src/tellus/contrato/regras.py` (#96): checa a versão, o modelo e a geometria e devolve o pedido normalizado com `hash_pedido`
- [X] T015 [US1] Rotas em `backend/src/tellus/api/contrato.py`: `GET /api/contrato/versao`, `GET /api/contrato/esquema`, `POST /api/contrato/pedido/validar`. O router trata os próprios erros com o envelope unificado
- [X] T016 [US1] `backend/src/tellus/contrato/exemplos.py`: gera `contracts/pedido.schema.json`, `contracts/resposta.schema.json` e `contracts/exemplos/*.json` (pedido válido, versão incompatível, geometria inválida, resposta Rio Verde com 006/007 reais)

## Phase 4: Polish

- [X] T017 [P] Rodar `python -m tellus.contrato.exemplos` e conferir os arquivos em `specs/011-contrato-api/contracts/`
- [X] T018 [P] Varrer a resposta por token e segredo (`backend/tests/contrato/test_resposta.py`)
- [X] T019 Suíte inteira `cd backend && uv run pytest -q` verde; `graphify update .`

## Dependencies

T001–T002 → T003–T005 → testes T006–T012 (paralelos) → T013–T016 → T017–T019.
#71/D-009 não bloqueia: os limites sem decisão ficam `decisao_pendente`.

## Parallel Example

T006, T007, T008, T009, T010, T011 e T012 estão em arquivos distintos e podem ser escritos em paralelo.

## Implementation Strategy

O MVP é a US1 inteira. A 008 entra depois como MENOR (nova seção ou novo adaptador), sem quebrar a 1.x.
