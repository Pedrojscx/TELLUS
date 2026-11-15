# Quickstart: validar o contrato 011

Pré-requisito: `cd backend && uv sync`. Não precisa de rede: os exemplos usam a série versionada de Rio Verde/GO.

1. Testes do contrato: `uv run pytest -q tests/contrato`. Esperado: todos passam.
   - Versão: um pedido com MAIOR diferente vira `versao_incompativel` e lista as versões aceitas.
   - Pedido: com um campo ausente ou uma geometria inválida, o cálculo não inicia e a resposta traz um erro claro.
   - Resposta: o exemplo gravado não tem número sem proveniência completa (`regras.numeros_sem_proveniencia == []`).
   - Fontes: com cache, a resposta sai `final_com_cache` e traz a data. Sem cache, sai `erro` com `final=false`, origem e código.
   - Contextos: a resposta valida com e sem 009/010. O `hash_principal` não muda.
   - Determinismo: o mesmo pedido gera a mesma resposta (JSON idêntico).
2. Regenerar os esquemas e os exemplos: `uv run python -m tellus.contrato.exemplos ../specs/011-contrato-api/contracts`. O `git diff` deve sair vazio quando nada mudou.
3. Rotas, com o router incluído (ver NOTA, trecho do app.py):
   - `GET /api/contrato/versao` → versão e regra.
   - `GET /api/contrato/esquema` → JSON Schema do pedido e da resposta.
   - `POST /api/contrato/pedido/validar` com `contracts/exemplos/pedido_valido.json` → 200 e pedido normalizado. Com `pedido_versao_incompativel.json` → 422 `versao_incompativel`.
4. Suíte inteira: `uv run pytest -q`.
