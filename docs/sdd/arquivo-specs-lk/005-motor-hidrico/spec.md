# Feature Specification: Motor hídrico e perda de produtividade

**Feature Branch**: `005-motor-hidrico`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "005-motor-hidrico: para cada ano do histórico, simular a segunda safra plantada após a colheita da soja: ETo FAO-56 a partir do clima (002), Kc e fases (004), balanço diário de água no solo, ETa e perda relativa de produtividade pela FAO-33 (Ky). Entregar o risco de falta de água e os cenários (percentis 25, 50 e 75) de cada cultura. Reproduzir um caso calculado à mão."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Risco de falta de água por cultura (Priority: P1)

O produtor informa a data de colheita da soja e a água disponível do solo. Para milho, sorgo e
cobertura, o TELLUS simula a safra em cada ano do histórico, como se tivesse plantado naquele
ano, e diz em quantos anos a falta de água tirou mais de 30% da produtividade.

**Why this priority**: é o núcleo do produto; o risco de falta de água é a metade "risco" da
decisão.

**Independent Test**: Rio Verde-GO, colheita da soja em 20/01, AD4: o milho 2ª safra mostra
número de anos simulados, a chance de perda maior que 30% e o déficit mediano; plantando em 05/03,
o risco do milho sobe claramente.

**Acceptance Scenarios**:

1. **Given** clima (002), parâmetros (004), local e data de colheita, **When** a simulação roda,
   **Then** cada cultura recebe: anos simulados, anos excluídos com motivo, chance de perda maior
   que 30%, déficit hídrico mediano na fase crítica e a perda relativa por ano.
2. **Given** duas datas de colheita, uma em janeiro e outra em março, **When** comparadas, **Then** o
   risco do milho é maior na data de março (sinal registrado no REGISTRO: chuva mediana de 193 mm
   no plantio de 20/01 contra 36 mm no de 05/03, dias 45 a 85).
3. **Given** um ano com chuva ausente na estação de cultivo, **When** a simulação roda, **Then** o
   ano é excluído e contado, nunca simulado com zero.

---

### User Story 2 - Cenários conservador, central e favorável (Priority: P1)

Para cada cultura, a perda relativa dos anos simulados vira três cenários de produtividade: o
conservador (percentil 25 da produtividade relativa), o central (mediana) e o favorável
(percentil 75). A economia (006) transforma esses cenários em margem.

**Why this priority**: resultado em faixas é exigência da constituição (Princípio II) e entrada da
spec 006.

**Independent Test**: com uma lista conhecida de perdas por ano, os três cenários batem com os
percentis calculados à mão.

**Acceptance Scenarios**:

1. **Given** as perdas por ano de uma cultura, **When** os cenários são calculados, **Then** saem
   as produtividades relativas nos percentis 25, 50 e 75, com o método de percentil declarado.
2. **Given** menos de 10 anos válidos, **When** os cenários são calculados, **Then** vêm com aviso de
   amostra pequena.

---

### User Story 3 - Caso calculado à mão confere com o motor (Priority: P1)

Um caso pequeno (por exemplo, 10 dias de clima fixo, um solo e uma cultura) é calculado à mão numa
planilha registrada no repositório. O motor reproduz cada número do caso.

**Why this priority**: Princípio IV; é o critério de aceite da regra no plano histórico.

**Independent Test**: rodar o motor no caso registrado e comparar ETo, ETc, água no solo, ETa e
perda dia a dia.

**Acceptance Scenarios**:

1. **Given** o caso à mão, **When** o motor roda, **Then** ETo, ETc, armazenamento, ETa e perda
   conferem dia a dia com tolerância de 0,1 mm (0,001 na perda relativa).
2. **Given** o mesmo pedido duas vezes, **When** o motor roda, **Then** as respostas são idênticas.

---

### Edge Cases

- Data de plantio = data de colheita da soja + intervalo de semeadura (padrão como hipótese
  editável). Se a data cair fora do ZARC, a simulação roda mesmo assim e a 007 mostra o aviso.
- Ciclo que passa do último dia com clima disponível no ano mais recente: o ano é excluído.
- Chuva acima da capacidade do solo: o excesso sai como drenagem/escoamento e não fica guardado.
- Começo do balanço: o solo começa com armazenamento definido (padrão: capacidade de campo após a
  soja, como hipótese editável) e isso aparece nas premissas.
- Radiação ausente em poucos dias: a ETo daquele dia usa a regra de preenchimento declarada (ou
  exclui o ano se passar de um limite), nunca valor inventado em silêncio.
- Cobertura não tem produtividade de grão: o motor entrega para ela o risco e o déficit; a perda
  relativa é usada pela 006 só se houver métrica de biomassa com fonte.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST calcular a ETo diária pelo método FAO-56 Penman-Monteith com as
  variáveis do POWER da 002 e a altitude do ponto.
- **FR-002**: O sistema MUST calcular a ETc diária com Kc por fase (004), interpolando o Kc na fase
  de desenvolvimento e na fase final como na FAO-56.
- **FR-003**: O sistema MUST fazer o balanço diário de água na zona radicular (chuva do IMERG da
  002, ETa, drenagem), com a água disponível do solo (004) e o fator de esgotamento p.
- **FR-004**: O sistema MUST calcular a perda relativa de produtividade de cada ano pela FAO-33:
  1 − Ya/Ym = Ky × (1 − ETa/ETc), por fase quando houver Ky por fase, ou total.
- **FR-005**: A data de plantio MUST ser a data de colheita da soja mais o intervalo de semeadura;
  a mesma data do calendário é aplicada a cada ano do histórico.
- **FR-006**: Anos sem dado suficiente MUST ser excluídos e contados, com motivo.
- **FR-007**: Por cultura, o sistema MUST entregar: anos simulados, anos excluídos, chance de perda
  maior que 30%, déficit mediano na fase crítica, perda por ano e os cenários P25, P50 e P75 da
  produtividade relativa.
- **FR-008**: As regras de cálculo MUST ser puras: sem rede, sem relógio, sem estado global
  (Princípio IV).
- **FR-009**: O mesmo pedido MUST produzir a mesma resposta, verificado por teste automático.
- **FR-010**: Um caso calculado à mão MUST estar registrado no repositório e o motor MUST
  reproduzi-lo (tolerâncias da User Story 3).
- **FR-011**: O limiar de "perda severa" (30%), o intervalo de semeadura e o armazenamento inicial
  MUST ser premissas editáveis, marcadas como hipótese até terem fonte.
- **FR-012**: A resposta MUST dizer que a frequência é histórica e não é previsão (Princípio II).

### Key Entities

- **Pedido de simulação**: local, data de colheita da soja, água disponível, cultura, grupo de
  cultivar, premissas editadas.
- **Ano simulado**: ano, data de plantio, ETo e ETc acumuladas, ETa, déficit por fase, perda
  relativa, situação (válido ou excluído com motivo).
- **Resultado por cultura**: anos válidos e excluídos, chance de perda severa, déficit mediano,
  cenários P25/P50/P75.
- **Caso de referência**: entradas fixas e saídas dia a dia calculadas à mão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O caso à mão confere em 100% dos dias, dentro da tolerância.
- **SC-002**: Uma simulação completa (3 culturas, todos os anos) para Rio Verde-GO responde em menos
  de 3 segundos com dados guardados.
- **SC-003**: Em Rio Verde-GO, o risco do milho aumenta de forma monótona entre plantios de 20/01,
  05/02, 20/02 e 05/03 (coerente com o REGISTRO e o ZARC).
- **SC-004**: 100% das respostas trazem os anos excluídos e o aviso de que não é previsão.

## Assumptions

- Um ano por simulação, com a mesma data de plantio no calendário (método do plano histórico).
- Chuva efetiva = chuva do IMERG sem correção; o viés local fica visível na 002.
- O intervalo de semeadura padrão é de 3 dias após a colheita da soja (hipótese).
- O armazenamento inicial padrão é a capacidade de campo (hipótese), justificado pela soja recém
  colhida no período chuvoso.
- A "fase crítica" de cada cultura (florescimento e enchimento de grãos) vem das fases da 004.
- Modelo de balanço de um único reservatório (bucket) da FAO-56, sem capilaridade nem lençol.
