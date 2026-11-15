# Feature Specification: Interface web

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Guiar produtor por área, colheita, solo, grupo, premissas, resultados, fontes e estados de erro.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Concluir comparação (Priority: P1)

Como produtor, quero informar dados da lavoura e entender a recomendação com suas fontes.

**Why this priority**: É o fluxo principal do produto.

**Independent Test**: Um produtor completa o caso Rio Verde/GO e encontra alternativas, avisos e fontes sem ajuda externa.

**Acceptance Scenarios**:

1. **Given** área confirmada, **When** informo colheita, solo e grupo, **Then** posso escolher metodologia e calcular.
2. **Given** resultado, **When** abro uma alternativa, **Then** vejo risco, margem, cenários, premissas e fontes.

### Edge Cases

- Carregamento informa etapa e não mostra resultado parcial como final.
- Erro de fonte mostra origem, cache disponível e ação possível.

## Requirements *(mandatory)*

- **FR-001**: A interface MUST oferecer os três modos de localização e confirmação no mapa.
- **FR-002**: A interface MUST solicitar data exata de colheita, textura ou mm e grupo I, II, III ou “não sei”.
- **FR-003**: A interface MUST oferecer as duas metodologias e explicar a diferença.
- **FR-004**: A interface MUST permitir editar premissas e comparar valor padrão e editado.
- **FR-005**: A interface MUST mostrar fontes, unidades, escala, qualidade, estados de carga e erros em PT-BR.

### Key Entities *(include if feature involves data)*

- **Sessão de comparação**: entradas confirmadas, metodologia, resultado, avisos e edição.

## Success Criteria *(mandatory)*

- **SC-001**: Em teste de usabilidade, 5 de 5 participantes concluem o caso de referência sem inserir dado fora do ZARC.
- **SC-002**: 100% dos estados de fonte indisponível mostram origem e data de cache ou erro legível.

## Assumptions

- [NEEDS CLARIFICATION: Quais requisitos de acesso e dispositivos são obrigatórios no lançamento inicial?]
