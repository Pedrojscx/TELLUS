# Feature Specification: Umidade SMAP

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Mostrar umidade do solo SMAP como contexto regional com aviso de escala.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver contexto regional (Priority: P1)

Como produtor, quero ver o contexto regional de umidade sem confundir a célula com minha lavoura.

**Why this priority**: O dado ajuda interpretação, mas tem escala ampla.

**Independent Test**: A tela associa cada valor a produto, célula, período, unidade, qualidade e aviso de escala.

**Acceptance Scenarios**:

1. **Given** dado válido, **When** abro contexto, **Then** vejo escala espacial e temporal junto do valor.
2. **Given** célula sem dado, **When** abro contexto, **Then** vejo indisponibilidade sem substituição.

### Edge Cases

- Dado regional nunca se apresenta como medição da fazenda ou previsão.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST tratar SMAP apenas como contexto regional.
- **FR-002**: O sistema MUST exibir produto, versão, célula, período, unidade, qualidade e resolução.
- **FR-003**: O sistema MUST mostrar aviso explícito de escala.
- **FR-004**: O sistema MUST NOT usar SMAP como única entrada de recomendação ou produtividade.

### Key Entities *(include if feature involves data)*

- **Contexto de umidade**: produto, célula, período, unidade, qualidade, escala e aviso.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos valores SMAP exibidos trazem aviso de escala.
- **SC-002**: 100% dos testes de célula ausente mostram indisponibilidade.

## Assumptions

- [NEEDS CLARIFICATION: Qual produto SMAP e regra de período serão usados como contexto regional?]
