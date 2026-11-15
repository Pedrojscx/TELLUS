# Constituição do TELLUS

TELLUS é uma ferramenta de apoio à decisão da segunda safra (milho 2ª safra, sorgo ou planta de
cobertura) para o produtor de soja do Cerrado. Usa dados NASA e fontes oficiais brasileiras.
Projeto do NASA Space Apps 2026, desafio Field Shift.

## Core Principles

### I. Todo número tem fonte

- Todo valor exibido ou usado em cálculo (clima, custo, preço, produtividade, Kc, Ky, duração de
  fase, janela ZARC, parâmetro de solo) MUST trazer fonte, data de obtenção e unidade.
- Valor sem fonte MUST ser marcado `"status": "hipotese"`, editável na interface e exibido como
  hipótese. Nenhuma constante sem fonte pode entrar em código sem essa marca.
- Parâmetros ficam em arquivos de referência versionados, nunca escritos direto no código.

Motivo: a margem por hectare é o único diferencial sobre o ZARC. Sem fonte, o produto vira um ZARC
pior, com números inventados (conselho, risco 1).

### II. Honestidade sobre a incerteza

- O resultado MUST ser apresentado como estimativa regional em faixas (cenários conservador,
  central e favorável), nunca como resposta para um talhão.
- Frequência histórica MUST NOT ser apresentada como previsão.
- Limitações conhecidas de cada fonte (resolução da grade, falhas, viés medido) MUST aparecer na
  tela de fontes ou em avisos da resposta.

### III. Chuva só de fonte validada

- A chuva vem de uma fonte plugável. Referência local: estação INMET A025 com controle de
  cobertura. Grade para o histórico: IMERG Final (GPM, NASA), com o viés local exibido.
- A chuva do NASA POWER MUST NOT entrar no balanço hídrico, nem crua nem com correção automática:
  a pesquisa de 14/11 mediu viés de -27% (jan a jun) a -56% (2025) contra a estação.
- O POWER continua sendo a fonte de temperatura, radiação, umidade e vento para a ETo.
- Fill values (-999 e equivalentes) MUST NOT entrar em cálculo.

### IV. Regras puras e verificáveis

- Balanço hídrico, produtividade e economia ficam em código puro, sem rede e sem estado global.
- Cada regra MUST reproduzir um caso calculado à mão e registrado no repositório, com teste
  automático.
- O mesmo pedido MUST gerar a mesma resposta (teste de determinismo).

### V. Funciona offline na demonstração

- Toda resposta de fonte externa é guardada em cache local com metadados (URL, data, parâmetros).
- Se a fonte estiver fora do ar, o sistema MUST usar o cache e avisar a data dele na resposta.
- A demonstração MUST rodar sem internet depois da primeira carga, iniciada por um comando.

### VI. Escopo mínimo até o fluxo completo

- Primeiro o fluxo único: localização e data de colheita da soja levam às três opções lado a
  lado, com risco de falta de água, margem em três cenários, janela ZARC ao lado e fontes.
- Extras (NDVI/vegetação, umidade do solo por satélite, sequências de várias safras) só entram
  depois do fluxo completo funcionando em `main`, e cada um em sua própria spec.
- Uma spec que não serve ao fluxo único antes do congelamento é adiada, não encolhida às pressas.

### VII. Segredos fora do Git

- `.env` (ex.: `EARTHDATA_TOKEN`) e qualquer credencial MUST NOT ser lidos em log, impressos ou
  commitados. Exemplos de configuração usam `.env.example` sem valores reais.
- Dados brutos baixados ficam fora do Git; só entram a procedência (`FONTE.md`, `*.meta.json`).

## Restrições do projeto

- Prazo: 2026-11-15 12h BRT. Congelamento de funcionalidades às 08h; depois disso, só correções.
- Cobertura: qualquer ponto do Brasil. Onde faltar dado oficial do local (praça Conab, janela
  ZARC, estação INMET próxima), o sistema MUST usar a referência mais próxima e dizer qual é e a
  que distância está, ou declarar a lacuna. Nunca preencher em silêncio.
- Região da demonstração e validação: Rio Verde-GO (Conab, ZARC e estação A025 já conferidos).
- Ferramentas só gratuitas. Python gerenciado com `uv`. A pilha exata (backend e frontend) é
  definida no `plan.md` de cada spec, coerente entre specs.
- Idioma: interface, specs, commits e issues em português do Brasil.

## Fluxo de trabalho

- Toda funcionalidade nasce de uma spec do Spec Kit (`specs/NNN-nome/`): specify, clarify quando
  houver ambiguidade, plan, tasks, implement.
- Cada spec tem branch `NNN-nome` e uma issue com labels `area:*` e `tipo:*` (e `agente:*` quando
  delegada). O merge em `main` só acontece com os testes da spec passando.
- `main` MUST rodar sempre. Decisões, evidências e bloqueios vão para `REGISTRO.md`.

## Governance

- Esta constituição prevalece sobre o `docs/PLANO.md` (histórico) e sobre preferências de agentes.
- Emendas: qualquer membro propõe por commit que altera este arquivo, com o motivo na mensagem.
  Versionamento semântico: MAJOR para remover ou redefinir princípio, MINOR para adicionar
  princípio ou seção, PATCH para redação.
- Todo `plan.md` MUST passar pela verificação de constituição (Constitution Check) antes das tasks;
  violação exige justificativa registrada no próprio plano.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
