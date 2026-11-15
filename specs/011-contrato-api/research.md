# Research: 011 Contrato de API

## R1. Versionamento

- **Decisão**: semver `MAIOR.MENOR.CORREÇÃO` em `versao_contrato`, no pedido e na resposta. O servidor aceita pedidos com o **mesmo MAIOR** e MENOR ≤ o seu. Os demais recebem o erro `versao_incompativel` (HTTP 422), com `versoes_aceitas`.
- **Regra de mudança**: remover ou renomear campo, mudar tipo ou unidade, ou mudar o significado de um estado = MAIOR. Campo opcional novo ou seção nova = MENOR. Texto ou correção = CORREÇÃO.
- **Alternativas**: data no nome (`2026-11`), sem regra de compatibilidade; versão no caminho (`/v1/...`), que exigiria mexer nas rotas existentes.

## R2. Formato de erro (estado atual, a unificar)

| Módulo | Formato hoje |
|---|---|
| localizacao, car, zarc, culturas, motor, economia (`app.py::_erro`) | `{"erro": {codigo, mensagem, campo}}` |
| clima (`app.py::_erro_clima`) | `{"erro": {codigo, mensagem, origem}}` |
| umidade (010, no próprio router) | `{"erro": {codigo, mensagem, origem}}` |
| vegetacao (009, no próprio router) | `{"erro": {codigo, mensagem, origem, campo}}` |

- **Decisão**: o contrato adota a **união** `{"erro": {codigo, mensagem, origem, campo}}`. `origem` é a fonte ou o módulo, ou `"pedido"` quando o erro é de entrada. `campo` aponta o campo do pedido ou vale `null`.
- A mudança dos handlers existentes é **proposta** (NOTA), não aplicada.

## R3. Proveniência por número (SC-002, constituição I)

- **Decisão**: cada seção tem `proveniencia: [Proveniencia]`. Cada entrada traz os seis campos da constituição (fonte, versão, período, unidade, localização, qualidade) e `cobre`, uma lista de padrões de caminho (`cenarios.*.custo_r_ha`).
  - Um número de `conteudo` só é válido se algum padrão com proveniência completa cobrir o seu caminho.
  - O teste percorre a resposta inteira.
  - A qualidade de uma hipótese é declarada como tal (`"hipotese"`), nunca como vazio.
- **Alternativa descartada**: proveniência embutida em cada número (`{valor, fonte...}`). Ela mudaria o formato real da 006/007, que o contrato só embala.
- Os **contextos 009/010** ficam fora dessa regra de cobertura. Eles trazem a proveniência do próprio módulo, verificada nas specs 009/010 (SC-001 de cada uma). O contrato só garante que eles estejam isolados.

## R4. Seções e a 008

- `risco_hidrico` (006) e `economia` (007) usam a saída **real** dos módulos na main (f03d966). Os adaptadores leem só campos existentes. Um campo que falte gera proveniência incompleta, e o teste acusa.
- `recomendacao` (008) fica com `estado: "pendente"`, `conteudo: null`, a proveniência da spec e nenhum campo de ranking.
- **Estado geral**:
  - `final` = todas as seções obrigatórias disponíveis e nenhuma fonte em falha;
  - `final_com_cache` = idem, com alguma fonte vinda do cache;
  - `incompleto` = há seção obrigatória pendente ou indisponível;
  - `erro` = fonte obrigatória falhou sem cache.
  - Hoje, com a 008 pendente, toda resposta é `incompleto`, e isso é declarado.

## R5. Contextos opcionais (#99)

- `contextos.vegetacao` e `contextos.umidade` recebem `estado` (`disponivel`, `indisponivel`, `erro` ou `nao_solicitado`), `conteudo` opaco (a resposta do módulo), `avisos` e `erro`.
- O hash das seções principais é calculado sem os contextos. O teste compara a resposta com e sem contextos e com contexto em erro.

## R6. D-009 (limites)

Ver `decisao-proposta.md`. A geometria usa o limite já aplicado pelo CAR: 5000 vértices por anel, `hipotese` em `referencias/car/limites.json`. Tamanho de arquivo e prazo de processamento ficam como `decisao_pendente`, sem valor (`null`).
