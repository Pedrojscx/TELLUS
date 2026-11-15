# Feature Specification: Calendário ZARC

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Ingerir ZARC por município, cultura, solo, grupo de cultivar e decêndio, a partir do SISZARC, para todas as UFs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver plantios permitidos (Priority: P1)

Como produtor, quero ver apenas decêndios ZARC válidos para minha lavoura e cultura.

**Why this priority**: A recomendação não pode sugerir plantio fora da janela oficial.

**Independent Test**: Um município, cultura, solo e grupo conhecidos retornam os mesmos decêndios e riscos do relatório oficial.

**Acceptance Scenarios**:

1. **Given** dados completos, **When** consulto calendário, **Then** vejo somente decêndios com risco oficial diferente de zero.
2. **Given** grupo “não sei”, **When** consulto, **Then** vejo o resultado separado para todos os grupos disponíveis.

### Edge Cases

- Município sem registro ou combinação ausente informa indisponibilidade, sem inferir janela vizinha.
- Decêndio fora da janela não entra em recomendação.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST guardar safra, portaria, município, UF, manejo, cultura, grupo, classe AD, decêndio e risco ZARC.
- **FR-002**: O sistema MUST obter os relatórios SISZARC sem login conforme a sequência documentada em registro da equipe.
- **FR-003**: O sistema MUST manter data de obtenção e vigência de cada conjunto.
- **FR-004**: O sistema MUST bloquear sugestão de plantio fora da janela ZARC.
- **FR-005**: O sistema MUST separar risco ZARC de risco histórico de falta de água.

### Key Entities *(include if feature involves data)*

- **Entrada ZARC**: safra, portaria, combinação agrícola, decêndio, risco e proveniência.

## Success Criteria *(mandatory)*

- **SC-001**: 100% dos decêndios exibidos para Rio Verde/GO nos grupos existentes conferem com o relatório SISZARC salvo.
- **SC-002**: 100% das recomendações contêm um decêndio ZARC válido.

## Assumptions

- SISZARC permanece acessível sem login para as consultas descritas.
