# Feature Specification: Identidade visual

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Criar identidade visual posterior ao fluxo funcional, sem esconder fontes, avisos ou acesso.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reconhecer o produto (Priority: P1)

Como produtor, quero reconhecer o Tellus e ler resultados e avisos com facilidade.

**Why this priority**: A identidade deve reforçar confiança depois que o fluxo existir.

**Independent Test**: Protótipo aprovado mantém leitura de resultado, fonte, hipótese e erro.

**Acceptance Scenarios**:

1. **Given** uma tela de resultado, **When** aplico a identidade aprovada, **Then** fonte, hipótese e aviso continuam visíveis.

### Edge Cases

- Nenhuma escolha de cor pode ser o único sinal de hipótese, erro ou qualidade.

## Requirements *(mandatory)*

- **FR-001**: A identidade MUST ser criada após validação do fluxo funcional.
- **FR-002**: A identidade MUST definir uso de marca, cor, texto e elementos gráficos com licença registrada.
- **FR-003**: A identidade MUST manter contraste e sinais textuais para fonte, hipótese, aviso e erro.
- **FR-004**: A identidade MUST não alterar o sentido de risco histórico como previsão.

### Key Entities *(include if feature involves data)*

- **Guia de identidade**: elementos aprovados, uso, licença, data e responsáveis.

## Success Criteria *(mandatory)*

- **SC-001**: 100% das telas principais mantêm fonte, hipótese e erro visíveis após aplicação.
- **SC-002**: 100% dos elementos de terceiros têm licença registrada.

## Assumptions

- Resolvido em 15/11 (D-011), por escolha do LK: nome TELLUS; paleta "Safra" (verde-folha #2F6B2F, dourado escuro #7A5C00, fundo marfim #FFFDF7; estados fonte #155E75, hipótese #7A5C00, aviso #9A3412, erro #B91C1C, todos ≥ 4,5:1); tom técnico e direto; nenhum elemento de terceiros na identidade (ícones e marca da equipe, fontes do sistema). Guia em `docs/marca/GUIA_DE_MARCA.md`.
