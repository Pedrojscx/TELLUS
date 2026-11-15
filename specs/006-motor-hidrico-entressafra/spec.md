# Feature Specification: Motor hídrico e entressafra

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Calcular risco histórico de falta de água por cultura e decêndio, incluindo entressafra, pousio e cobertura.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparar água por alternativa (Priority: P1)

Como produtor, quero comparar o risco de falta de água das alternativas permitidas após minha colheita.

**Why this priority**: Este cálculo sustenta a decisão agrícola.

**Independent Test**: Um caso documentado à mão produz o mesmo resultado no motor, sem rede.

**Acceptance Scenarios**:

1. **Given** entradas completas e decêndio ZARC válido, **When** calculo, **Then** vejo risco, déficit e série histórica usados.
2. **Given** pousio ou cobertura, **When** calculo safra seguinte, **Then** vejo a premissa e o efeito entre colheita e plantio.

### Edge Cases

- Dia climático ausente interrompe a série e gera aviso.
- Sem parâmetro fonte, o resultado mostra hipótese ou não calcula.

## Requirements *(mandatory)*

- **FR-001**: O motor MUST ser puro, sem rede, relógio ou estado oculto.
- **FR-002**: O motor MUST calcular cada cultura × decêndio somente dentro da janela ZARC.
- **FR-003**: O motor MUST receber chuva, ETo, solo, cultura e estado inicial como entradas rastreáveis.
- **FR-004**: O motor MUST representar intervalo entre colheita e plantio com pousio ou cobertura explícitos.
- **FR-005**: O motor MUST devolver risco histórico e déficit, sem chamar frequência de previsão.

### Key Entities *(include if feature involves data)*

- **Simulação hídrica**: entradas versionadas, período, déficit, risco e avisos.
- **Entressafra**: início, fim, manejo, fonte e efeito no estado hídrico.

## Success Criteria *(mandatory)*

- **SC-001**: O teste do caso feito à mão passa com tolerância declarada e sem acesso à rede.
- **SC-002**: 100% das simulações têm versões de todas as entradas.

## Assumptions

- [NEEDS CLARIFICATION: Qual estado inicial de água e regra de pousio/cobertura terão fonte para cada simulação?]
