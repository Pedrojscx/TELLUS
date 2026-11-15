# Feature Specification: Pesquisa CAR WFS

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Investigar a consulta de imóvel rural pelo número do CAR e manter upload do arquivo SICAR como alternativa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificar um CAR (Priority: P1)

Como produtor, quero informar meu número do CAR para saber se o sistema pode localizar o imóvel.

**Why this priority**: Reduz a entrada manual quando a fonte pública permitir.

**Independent Test**: Um código válido, inválido e inexistente recebem estados distintos e auditáveis.

**Acceptance Scenarios**:

1. **Given** uma fonte acessível e código válido, **When** o produtor consulta, **Then** o sistema informa se recebeu geometria e sua origem.
2. **Given** código inexistente ou fonte sem dado, **When** consulta, **Then** o sistema não inventa geometria e oferece upload SICAR.

### Edge Cases

- Fonte WFS fora do ar: informar origem e alternativa de upload.
- Geometria inválida: não aceitar como área de cálculo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST registrar código consultado, data, fonte, versão e resultado.
- **FR-002**: O sistema MUST distinguir CAR inexistente, fonte indisponível e resposta sem geometria.
- **FR-003**: O sistema MUST oferecer upload do shapefile exportado do SICAR como alternativa.
- **FR-004**: O sistema MUST exigir confirmação da geometria antes de usá-la.

### Key Entities *(include if feature involves data)*

- **Consulta CAR**: código, data, resultado, origem e qualidade.
- **Geometria SICAR**: polígono, origem, validade e estado de confirmação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos testes de códigos válido, inválido e inexistente exibem um estado distinto.
- **SC-002**: 100% das geometrias aceitas mostram fonte e data.

## Assumptions

- Resolvido em 15/11 (D-001): o WFS público do SICAR (`geoserver.car.gov.br/geoserver/sicar/wfs`, camada `sicar:sicar_imoveis_<uf>`) aceita filtro por `cod_imovel` sem login e devolve o polígono do imóvel; código inexistente devolve zero feições. A geometria é a declarada no CAR (pode estar "aguardando análise") e continua exigindo confirmação do produtor.
- A pesquisa não promete acesso automático até a validação.
