# Feature Specification: Vegetação MODIS e HLS

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Mostrar contexto histórico de sazonalidade e cobertura da área, sem estimar produtividade.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver contexto de cobertura (Priority: P1)

Como produtor, quero ver a sazonalidade histórica da minha área para interpretar a recomendação.

**Why this priority**: Acrescenta contexto sem prometer produtividade.

**Independent Test**: Uma série mostra produto, período, resolução, qualidade e aviso de limite.

**Acceptance Scenarios**:

1. **Given** observações válidas, **When** abro contexto, **Then** vejo série e qualidade.
2. **Given** nuvem ou dado sem qualidade, **When** abro contexto, **Then** vejo lacuna, não valor estimado.

### Edge Cases

- HLS indisponível por credencial não bloqueia o fluxo principal.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST mostrar MODIS e HLS como contexto histórico.
- **FR-002**: O sistema MUST exibir produto, versão, período, resolução, unidade e qualidade.
- **FR-003**: O sistema MUST aplicar regra documentada de qualidade.
- **FR-004**: O sistema MUST NOT converter vegetação em produtividade.

### Key Entities *(include if feature involves data)*

- **Observação de vegetação**: produto, data, valor, qualidade, resolução e área.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos indicadores exibem escala e limitação.
- **SC-002**: Nenhum texto de resultado afirma produtividade derivada da vegetação.

## Assumptions

- [NEEDS CLARIFICATION: Qual índice, período mínimo e regra de qualidade respondem à pergunta de contexto da área?]
