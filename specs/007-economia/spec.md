# Feature Specification: Economia

**Feature Branch**: `sdd/etapa-1`  
**Created**: 2026-11-14  
**Status**: Draft

**Input**: Calcular margem por hectare com custos Conab e preços CEPEA/ESALQ editáveis.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conferir margem e premissas (Priority: P1)

Como produtor, quero ver a margem de cada cenário e editar preço ou custo para testar minha realidade.

**Why this priority**: A recomendação deve mostrar efeito econômico verificável.

**Independent Test**: Uma troca de custo ou preço atualiza a margem e mantém origem dos dois valores.

**Acceptance Scenarios**:

1. **Given** praça Conab compatível, **When** comparo, **Then** vejo praça, distância, mês, lista de custo e unidade R$/ha.
2. **Given** nova premissa, **When** edito, **Then** vejo margem anterior e nova, com estado da fonte.

### Edge Cases

- Município sem praça Conab compatível informa ausência e não escolhe praça sem mostrar distância.
- Cobertura sem custo ou preço fonte aparece como hipótese, sem margem apresentada como fato.

## Requirements *(mandatory)*

- **FR-001**: O sistema MUST selecionar a praça Conab mais próxima com a mesma cultura e mostrar distância.
- **FR-002**: O sistema MUST mostrar lista de itens de custo, mês, sistema, unidade e fonte.
- **FR-003**: O sistema MUST usar preço CEPEA/ESALQ quando existir e registrar praça, data e unidade.
- **FR-004**: O sistema MUST permitir substituir toda premissa econômica.
- **FR-005**: O sistema MUST calcular margem por hectare para cenários conservador, central e favorável.

### Key Entities *(include if feature involves data)*

- **Premissa econômica**: preço ou custo, valor, unidade, fonte, data, praça e estado.
- **Margem**: receita, itens de custo, cenário, unidade e versões de premissas.

## Success Criteria *(mandatory)*

- **SC-001**: 100% das margens mostram todos os itens e premissas usados.
- **SC-002**: 100% dos custos Conab mostram praça e distância.

## Assumptions

- Resolvido em 15/11 (D-005), seguindo a recomendação (não inventar preço): o CEPEA publica o Indicador do Milho ESALQ/BM&FBovespa (Campinas-SP, R$/saca de 60 kg, à vista), usado para o milho. Não há indicador CEPEA de sorgo (a lista de indicadores não inclui sorgo), e o portal de preços da Conab apresenta certificado inválido, então não há fonte segura. O preço do sorgo fica indisponível até o produtor informar, sem margem factual. A planta de cobertura não é comercializada: a receita é zero e o custo deve ser informado (não há planilha Conab).
