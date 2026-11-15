# Feature Specification: Localização da propriedade

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Localizar lavoura por desenho no mapa, arquivo georreferenciado ou CAR, para todos os estados brasileiros.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Informar a lavoura (Priority: P1)

Como produtor, quero desenhar, marcar ou enviar minha área para receber resultado da lavoura certa.

**Why this priority**: A área define células, município e resultados seguintes.

**Independent Test**: Cada modo entrega uma geometria válida, confirmada e com área exibida.

**Acceptance Scenarios**:

1. **Given** um polígono válido, **When** confirmo, **Then** vejo o limite, área e município identificados.
2. **Given** KML, KMZ, GeoJSON ou Shapefile .zip válido, **When** envio, **Then** vejo o mesmo resumo antes de continuar.

### Edge Cases

- Arquivo sem geometria, com formato não aceito ou polígono inválido gera erro claro.
- Área que cruza municípios preserva a geometria e informa todos os municípios atingidos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar desenho, marcação, KML, KMZ, GeoJSON e Shapefile .zip.
- **FR-002**: O sistema MUST validar geometria antes de calcular qualquer resultado.
- **FR-003**: O sistema MUST mostrar área, unidade, geometria e municípios associados antes da confirmação.
- **FR-004**: O sistema MUST permitir corrigir ou substituir a área confirmada.
- **FR-005**: O sistema MUST preservar fonte e data da geometria, inclusive quando vier do CAR.

### Key Entities *(include if feature involves data)*

- **Lavoura**: geometria confirmada, área, unidade, municípios e origem.
- **Arquivo georreferenciado**: formato, conteúdo, estado de validação e origem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos seis modos de entrada aceitos passam por confirmação antes de alimentar cálculo.
- **SC-002**: 100% dos arquivos inválidos retornam erro que nomeia o problema.

## Assumptions

- A seleção representa uma lavoura por solicitação.
- Consulta CAR depende da pesquisa CAR WFS.
