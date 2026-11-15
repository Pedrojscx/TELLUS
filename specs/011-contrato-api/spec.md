# Feature Specification: Contrato de API

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Definir contrato versionado para pedidos, resultados, fontes, premissas e erros.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber resultado rastreável (Priority: P1)

Como interface, quero receber um resultado completo e versionado para mostrar ao produtor sem mudar seu sentido.

**Why this priority**: Liga o fluxo a dados e cálculo reproduzíveis.

**Independent Test**: Um pedido válido e uma resposta gravada passam na validação da versão.

**Acceptance Scenarios**:

1. **Given** pedido válido, **When** calculo, **Then** recebo alternativas, premissas, fontes, qualidade e avisos.
2. **Given** fonte sem cache, **When** calculo, **Then** recebo erro com código, mensagem em PT-BR e origem.

### Edge Cases

- Versão incompatível retorna erro claro e versão aceita.
- Pedido com geometria inválida não inicia cálculo.

## Requirements *(mandatory)*

- **FR-001**: O contrato MUST ter versão explícita e regras de mudança incompatível.
- **FR-002**: O pedido MUST representar área, colheita, solo, grupo, metodologia e premissas editadas.
- **FR-003**: A resposta MUST representar alternativas, cenários, fontes, unidades, qualidade, cache e hipóteses.
- **FR-004**: O contrato MUST distinguir resultado, aviso e erro por fonte.
- **FR-005**: O contrato MUST permitir contexto opcional de vegetação e SMAP sem alterar resultado principal.

### Key Entities *(include if feature involves data)*

- **Pedido de cálculo**: versão, área, entradas, premissas e metodologia.
- **Resposta de cálculo**: alternativas, proveniência, avisos, erros e versão.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos exemplos válidos e de erro passam na validação da versão.
- **SC-002**: 100% dos números do exemplo de resposta têm proveniência completa.

## Assumptions

- [NEEDS CLARIFICATION: Qual limite de tamanho e prazo de processamento será aceito para arquivo e geometria complexa?]
