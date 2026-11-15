# Feature Specification: Dados de clima

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Usar IMERG Final V07 diário para chuva, INMET para validação local e NASA POWER para variáveis de ETo, com cache persistente.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conferir a chuva usada (Priority: P1)

Como produtor, quero ver a chuva histórica da minha área e seus limites para avaliar a recomendação.

**Why this priority**: A chuva é entrada principal do risco hídrico.

**Independent Test**: Uma área que cruza células devolve média ponderada, células e qualidade.

**Acceptance Scenarios**:

1. **Given** área sobre uma ou mais células, **When** solicito série, **Then** recebo média ponderada pela área e cada célula usada.
2. **Given** fonte indisponível com cache, **When** solicito série, **Then** recebo cache com data e aviso.

### Edge Cases

- Célula ou dia sem dado não vira chuva zero.
- Falta de cache e fonte fora do ar retorna erro que cita a fonte.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST usar IMERG Final V07 diário como chuva principal e registrar versão, período, UTC, célula e qualidade.
- **FR-002**: O sistema MUST calcular chuva da área por média ponderada da interseção de células de 0,1°.
- **FR-003**: O sistema MUST obter temperatura, radiação, umidade e vento de NASA POWER; chuva POWER MUST NOT entrar no cálculo.
- **FR-004**: O sistema MUST mostrar validação local pela estação INMET mais próxima e separar essa validação da série usada.
- **FR-005**: O sistema MUST manter cache versionado e reproduzir o mesmo pedido com o mesmo cache.

### Key Entities *(include if feature involves data)*

- **Série climática**: variável, dia, unidade, cobertura, qualidade e proveniência.
- **Entrada de cache**: consulta, versão, data, hash, fonte e validade.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos valores climáticos devolvidos têm fonte, versão, unidade, período e localização.
- **SC-002**: O teste Rio Verde/GO reproduz a comparação de 1.218 dias: IMERG −1,03% de viés e MAE 4,13 mm/dia contra INMET A025, com o período e limites mostrados.
- **SC-003**: Dois pedidos iguais com o mesmo cache retornam respostas idênticas.

## Assumptions

- [NEEDS CLARIFICATION: Como tratar o período após set/2025 enquanto o catálogo IMERG Final consultado não o inclui?]
- Frequência histórica não é previsão.
