# Feature Specification: Base de solo e culturas

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Registrar parâmetros de solo e culturas com fontes, para milho, sorgo e planta de cobertura após soja.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Informar e conferir solo (Priority: P1)

Como produtor, quero informar textura e ajustar água disponível em milímetros com origem visível.

**Why this priority**: A água disponível muda o cálculo hídrico.

**Independent Test**: Cada textura mostra classe AD, valor em mm, fonte ou hipótese, e permite edição explícita.

**Acceptance Scenarios**:

1. **Given** textura arenosa, média ou argilosa, **When** seleciono, **Then** vejo a classe AD e valor em mm com fonte aplicável.
2. **Given** valor sem fonte, **When** o sistema o mostra, **Then** aparece como hipótese no resultado e no contrato.

### Edge Cases

- Cultura, UF ou textura sem fonte não recebe conversão inventada.
- Valor editado incompatível com unidade ou domínio gera erro claro.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST registrar capacidade de água, raiz, fases, ciclo, Kc e Ky com fonte, data, unidade e validade regional.
- **FR-002**: O sistema MUST oferecer texturas arenosa, média e argilosa, conversão para AD e edição avançada em mm.
- **FR-003**: O sistema MUST marcar e propagar `hipotese` quando faltar fonte.
- **FR-004**: O sistema MUST preservar parâmetros padrão e editados pelo produtor.
- **FR-005**: O sistema MUST usar FAO-56 e FAO-33 como método de referência sem tratá-los como fonte de parâmetro local.

### Key Entities *(include if feature involves data)*

- **Parâmetro agronômico**: nome, valor, unidade, fonte, data, validade regional e estado.
- **Premissa de solo**: textura, classe AD, mm, origem e edição.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos parâmetros usados pelo motor têm fonte completa ou status `hipotese`.
- **SC-002**: 100% das mudanças do produtor mostram valor anterior, novo valor e unidade.

## Assumptions

- [NEEDS CLARIFICATION: Qual fonte liga textura informada pelo produtor a classe AD e mm para cada cultura e UF?]
