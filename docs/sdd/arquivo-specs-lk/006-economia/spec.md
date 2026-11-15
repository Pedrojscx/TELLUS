# Feature Specification: Economia e margem por hectare

**Feature Branch**: `006-economia`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "006-economia: transformar os cenários de produtividade (005) em margem por hectare para milho 2ª safra, sorgo e cobertura, usando custos de produção da Conab da praça indicada pela 001, preço de venda com fonte e produtividade de referência da Conab. Mostrar quais custos entram, permitir editar tudo e marcar como hipótese o que não tiver fonte."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Margem por hectare em três cenários (Priority: P1)

Para cada opção, o produtor vê receita, custo e margem por hectare nos cenários conservador,
central e favorável, com a fonte do custo, do preço e da produtividade de referência.

**Why this priority**: a margem é o diferencial do TELLUS sobre o ZARC (conselho, risco 1).

**Independent Test**: Rio Verde-GO, milho 2ª safra, cenário central com produtividade relativa
1,0: produtividade 6.000 kg/ha (premissa Conab), custo operacional R$ 5.889/ha (Conab, março/2026)
e preço com fonte. A margem confere com a conta à mão.

**Acceptance Scenarios**:

1. **Given** os cenários da 005 e a praça Rio Verde-GO, **When** a margem é calculada, **Then** cada
   cultura mostra, por cenário: produtividade (kg/ha e sacas/ha), receita, custo e margem em R$/ha.
2. **Given** a margem exibida, **When** o usuário abre o detalhe, **Then** vê a lista de custos
   incluídos (nível de custo Conab escolhido) e a fonte e data de cada número.
3. **Given** uma praça Conab de outro município (aviso da 001), **When** a margem é exibida, **Then**
   o aviso aparece junto do custo.

---

### User Story 2 - Editar premissas e ver a margem mudar (Priority: P1)

O produtor sabe o próprio custo ou o preço negociado. Ele edita preço, custo ou produtividade de
referência, e a margem é recalculada na hora, com a marca de "valor editado".

**Why this priority**: premissas editáveis são verificação de qualidade do plano e condição do
conselho (sem fonte → editável marcado como hipótese).

**Independent Test**: alterar o preço do milho de um valor para outro e ver a margem mudar
exatamente (diferença de preço × produtividade).

**Acceptance Scenarios**:

1. **Given** o preço do sorgo editado, **When** recalculado, **Then** a receita e a margem mudam e o
   preço aparece como "editado pelo usuário" com o valor original ao lado.
2. **Given** a troca do nível de custo (custeio, custo variável, operacional ou total), **When**
   recalculado, **Then** a margem usa o novo nível e o rótulo informa qual é.

---

### User Story 3 - Planta de cobertura com custo e sem receita de grão (Priority: P2)

A cobertura não vende grão. O TELLUS mostra o custo dela por hectare e a margem negativa
correspondente, e lista os benefícios ao solo apenas como texto com fonte, sem inventar valor em
reais.

**Why this priority**: mantém a ligação com saúde do solo (decisão do coordenador) sem números
sem fonte.

**Independent Test**: a margem da cobertura é igual a menos o custo da cobertura; o benefício
aparece como texto com referência.

**Acceptance Scenarios**:

1. **Given** a cobertura, **When** a margem é calculada, **Then** receita é zero, custo vem da fonte
   ou de hipótese marcada, e a margem é negativa.
2. **Given** um benefício com fonte que tenha valor em reais (ex.: ganho medido na soja seguinte),
   **When** cadastrado nas referências, **Then** ele pode entrar como linha separada e opcional.

---

### Edge Cases

- A Conab não publica preço de venda nas planilhas de custo: o preço vem de outra fonte (ex.:
  preços agropecuários Conab ou CEPEA) ou é hipótese editável.
- Praça sem planilha da cultura (ex.: sorgo inexistente na praça mais próxima): usa a praça mais
  próxima que tenha a cultura e avisa a distância.
- Planilha de ano anterior: o ano e o mês de referência aparecem; não há correção monetária
  automática.
- Produtividade relativa negativa ou acima de 1 não existe: os cenários são limitados a 0..1.
- Unidade de preço em R$/saca de 60 kg; produtividade em kg/ha; conversão explícita.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ler das planilhas de custo da Conab, para a praça indicada pela 001 e
  para cada cultura, o custeio, o custo variável, o custo operacional, o custo total e a
  produtividade de referência, com ano, mês de referência e endereço da planilha.
- **FR-002**: O nível de custo padrão MUST ser o custo operacional (inclui depreciação, exclui
  remuneração de terra e capital), e o usuário MUST poder trocar o nível.
- **FR-003**: A produtividade de cada cenário MUST ser a produtividade de referência da Conab vezes
  a produtividade relativa do cenário (005).
- **FR-004**: Receita = produtividade × preço; margem = receita − custo do nível escolhido; tudo em
  R$/ha, com a fórmula visível.
- **FR-005**: O preço de venda de cada cultura MUST trazer fonte, praça, data e unidade, ou a marca
  de hipótese.
- **FR-006**: Preço, custo e produtividade de referência MUST ser editáveis por simulação, e a
  resposta MUST indicar o valor editado e o original.
- **FR-007**: A cobertura MUST ter receita de grão zero, custo com fonte ou hipótese, e benefícios
  ao solo como texto com referência; valor monetário de benefício só com fonte.
- **FR-008**: O sistema MUST guardar as planilhas e preços obtidos com procedência e funcionar sem
  rede com os dados guardados (Princípio V).
- **FR-009**: Para Rio Verde-GO, os custos e produtividades MUST conferir com a tabela do REGISTRO
  (soja 3.900 kg/ha; milho 2ª safra 6.000 kg/ha, custo operacional 5.889; sorgo 3.600 kg/ha, custo
  operacional 3.807; R$/ha, março/2026).
- **FR-010**: Os cálculos MUST ser puros e determinísticos, com um caso à mão registrado (Princípio
  IV).

### Key Entities

- **Planilha de custo**: praça, UF, cultura, safra, mês de referência, níveis de custo, produtividade
  de referência, fonte.
- **Preço de venda**: cultura, praça, data, valor, unidade, fonte ou hipótese.
- **Resultado econômico**: cultura, cenário, produtividade, receita, custo, margem, nível de custo,
  premissas editadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para Rio Verde-GO, 100% dos custos e produtividades conferem com o REGISTRO.
- **SC-002**: O caso à mão de margem confere ao centavo.
- **SC-003**: Uma edição de premissa recalcula a margem em menos de 1 segundo.
- **SC-004**: 100% dos números econômicos exibidos têm fonte ou marca de hipótese.

## Assumptions

- As planilhas Conab (série histórica por cultura, uma aba por município-ano) são a fonte de custo;
  o endereço está em `data/raw/conab/FONTE.md`.
- O preço de venda padrão vem da série de preços agropecuários da Conab (ou CEPEA) da praça mais
  próxima; a escolha exata da fonte de preço é tarefa do plano.
- A produtividade de referência da Conab é premissa ex-ante (não medição) e é tratada como a
  produtividade sem estresse hídrico (Ym) do local.
- O custo da cobertura (semente e operação) vem de fonte Embrapa ou fica como hipótese editável.
- Valores em reais correntes do mês de referência, sem atualização monetária.
