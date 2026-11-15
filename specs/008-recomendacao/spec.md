# Feature Specification: Recomendação

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Oferecer duas metodologias no mesmo motor: cultura escolhida e cálculo completo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher data para uma cultura (Priority: P1)

Como produtor, quero escolher uma cultura e receber os melhores decêndios permitidos.

**Why this priority**: Atende decisão direta de plantio.

**Independent Test**: Uma cultura retorna somente decêndios ZARC válidos, ordenados pelos mesmos resultados do motor.

### User Story 2 - Comparar alternativas (Priority: P2)

Como produtor, quero ordenar culturas e decêndios para ver o melhor par.

**Why this priority**: Atende quem ainda não escolheu cultura.

**Independent Test**: A ordem usa exatamente os resultados retornados pela metodologia de cultura escolhida.

**Acceptance Scenarios**:

1. **Given** cultura selecionada, **When** peço resultado, **Then** vejo decêndios válidos, risco e margens por cenário.
2. **Given** cálculo completo, **When** peço resultado, **Then** vejo culturas × decêndios ordenados e critérios claros.

### Edge Cases

- Grupo “não sei” mostra todos os grupos testados, sem ocultar diferença.
- Não há recomendação quando nenhuma combinação tiver dados completos.

## Requirements *(mandatory)*

- **FR-001**: As duas metodologias MUST usar o mesmo motor e as mesmas entradas versionadas.
- **FR-002**: O sistema MUST excluir decêndios fora do ZARC.
- **FR-003**: O sistema MUST mostrar risco hídrico e margem por hectare para os três cenários.
- **FR-004**: O sistema MUST exibir critérios de ordem e avisos de hipótese.
- **FR-005**: O sistema MUST separar risco ZARC, risco histórico e margem.

### Key Entities *(include if feature involves data)*

- **Alternativa**: cultura, grupo, decêndio, risco, cenário, margem e versões usadas.
- **Recomendação**: metodologia, critério de ordem, alternativas e avisos.

## Success Criteria *(mandatory)*

- **SC-001**: Para a mesma cultura e entradas, ambas as metodologias devolvem valores iguais por decêndio.
- **SC-002**: 100% das alternativas sugeridas passam na janela ZARC.

## Assumptions

- Resolvido em 15/11 (D-006): quartis da perda relativa simulada (006). Conservador = percentil 75 (pior em 1 de cada 4 anos), central = mediana, favorável = percentil 25. Não há fonte setorial obrigatória; é decisão de produto declarada (hipótese visível), editável pelo produtor (10/25/50/75/90) e mostrada em toda resposta.
