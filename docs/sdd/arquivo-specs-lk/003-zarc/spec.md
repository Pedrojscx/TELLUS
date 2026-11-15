# Feature Specification: Janelas e risco do ZARC

**Feature Branch**: `003-zarc`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "003-zarc: para o município do local (001), obter do ZARC oficial do MAPA (SISZARC) as janelas de semeadura e o risco por decêndio de milho 2ª safra, sorgo granífero 2ª safra, milho consorciado com braquiária e soja, por grupo de cultivar e tipo de solo, com portaria e safra; dizer, para uma data de plantio, se ela está na janela e com qual risco oficial."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber se a data de plantio está na janela oficial (Priority: P1)

O produtor informa (ou o sistema deriva) a data de plantio da segunda safra. Para cada cultura,
o TELLUS diz se a data cai dentro da janela do ZARC para o município, o grupo de cultivar e o tipo
de solo, e com qual risco oficial (20%, 30% ou 40%), citando a portaria.

**Why this priority**: o ZARC lado a lado é condição do conselho e define acesso a crédito e
seguro. É a referência contra a qual a margem do TELLUS mostra valor.

**Independent Test**: Rio Verde-GO, grupo I, plantio em 05/02, solo AD4: milho 2ª safra dá 20%
(Portaria 322); o mesmo dia em AD1 dá 40%.

**Acceptance Scenarios**:

1. **Given** Rio Verde-GO, milho 2ª safra, grupo I, **When** a data está nos decêndios 1 a 3 (1 a
   31 de janeiro), **Then** o risco é 20% em todos os solos, Portaria 322.
2. **Given** Rio Verde-GO, milho 2ª safra, grupo I, decêndio 6 (21 a 28 de fevereiro), **When** o
   solo é AD6, **Then** o risco é 30%; **When** o solo é AD5 ou menor, **Then** fica fora da janela.
3. **Given** Rio Verde-GO, sorgo 2ª safra, grupo I, solo argiloso, **When** o plantio é no
   decêndio 9 (21 a 31 de março), **Then** o risco é 30% (Portaria 273).
4. **Given** uma data depois do último decêndio da janela, **When** consultada, **Then** a resposta
   é "fora da janela do ZARC", nunca risco zero.

---

### User Story 2 - Ver a janela inteira de cada cultura (Priority: P2)

O usuário vê, para o município, a janela completa de cada cultura como uma linha do tempo por
decêndio, colorida pelo risco, para entender quanto tempo resta depois da colheita da soja.

**Why this priority**: ajuda a explicar a decisão, mas o fluxo funciona só com a consulta da data.

**Independent Test**: Rio Verde-GO, grupo I: a janela do sorgo em solo argiloso vai até um mês
depois da janela do milho.

**Acceptance Scenarios**:

1. **Given** Rio Verde-GO, **When** a janela é pedida, **Then** vem a lista de decêndios com o risco
   por solo e grupo, para cada cultura.
2. **Given** grupos de cultivar diferentes, **When** comparados, **Then** o grupo II do milho mostra
   janela mais curta que o grupo I, como registrado em 14/11.

---

### User Story 3 - Município sem zoneamento para uma cultura (Priority: P2)

Em muitos municípios uma das culturas não tem ZARC publicado. O TELLUS diz isso claramente, em vez
de mostrar janela vazia como se fosse risco alto.

**Why this priority**: cobertura nacional (escolha da 001) exige lidar com lacunas.

**Independent Test**: escolher um município sem portaria de sorgo e ver "sem ZARC publicado para
sorgo neste município", com a safra consultada.

**Acceptance Scenarios**:

1. **Given** um município sem portaria para a cultura, **When** consultado, **Then** a resposta
   declara a lacuna e a safra consultada.
2. **Given** o SISZARC fora do ar e o município já consultado antes, **When** consultado, **Then**
   vem o resultado guardado com a data da consulta.

---

### Edge Cases

- Fevereiro tem decêndio 6 de 21 a 28 (ou 29); o decêndio 36 vai de 21 a 31 de dezembro.
- A soja tem janela que cruza o ano (decêndios 28 a 36 e 1); a lógica de decêndio não pode quebrar
  na virada.
- Milho usa classes de água disponível (AD1 a AD6); sorgo pode vir por textura (arenoso, média,
  argiloso). A resposta guarda a classe na forma em que a portaria publica.
- Portaria nova publicada no meio da safra: vale a que o SISZARC lista como vigente na data da
  consulta, com número e data gravados.
- Sequeiro e irrigado: só sequeiro entra nesta spec.
- Planta de cobertura pura (ex.: milheto, braquiária solteira) não tem ZARC; a referência oficial
  mais próxima é milho com braquiária, mostrada como tal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Para o município (código IBGE) da 001, o sistema MUST obter do SISZARC, para a safra
  vigente e manejo sequeiro, as tabelas de risco por decêndio de: milho 2ª safra, sorgo granífero
  2ª safra, milho consorciado com braquiária e soja.
- **FR-002**: As tabelas MUST cobrir os grupos de cultivar I, II e III e todas as classes de solo
  publicadas para cada cultura.
- **FR-003**: Cada tabela MUST trazer o número e a data da portaria, a safra e a data da consulta
  (Princípio I).
- **FR-004**: Dada uma data, uma cultura, um grupo e uma classe de solo, o sistema MUST responder o
  decêndio, o risco oficial (20%, 30% ou 40%) ou "fora da janela", e a portaria.
- **FR-005**: O sistema MUST converter datas em decêndios no padrão do ZARC (36 por ano; decêndio 1
  = 1 a 10 de janeiro; o terceiro decêndio de cada mês vai até o fim do mês).
- **FR-006**: Ausência de portaria para a cultura no município MUST ser declarada como lacuna, nunca
  como fora da janela.
- **FR-007**: Respostas do SISZARC MUST ser guardadas com procedência e reutilizadas; sem acesso, o
  sistema MUST usar o guardado e informar a data (Princípio V).
- **FR-008**: O sistema MUST entregar a janela completa por cultura, grupo e solo, para a linha do
  tempo da interface.
- **FR-009**: A planta de cobertura MUST ser referida ao ZARC de milho com braquiária, com aviso de
  que não há zoneamento para cobertura pura.
- **FR-010**: Rio Verde-GO MUST reproduzir os valores registrados em 14/11 (Portarias 198, 273, 322 e
  337; grupos I, II e III), e os dados da demo MUST estar guardados para rodar sem rede.

### Key Entities

- **Portaria ZARC**: número, data, cultura, UF, safra, manejo.
- **Tabela de risco**: município, cultura, grupo de cultivar, classe de solo, risco por decêndio.
- **Consulta de data**: data, decêndio, cultura, grupo, solo, risco ou fora da janela ou lacuna,
  portaria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para Rio Verde-GO, 100% dos riscos conferem com os registrados no REGISTRO.md.
- **SC-002**: A conversão de data em decêndio acerta 100% das datas de um ano inteiro, incluindo
  bissexto e virada de ano.
- **SC-003**: Um município novo, com internet, tem as quatro culturas consultadas em menos de 1
  minuto.
- **SC-004**: Toda resposta de risco mostra a portaria; nenhuma sem ela.

## Assumptions

- O SISZARC responde a POST simples sem login, na sequência registrada em 14/11
  (`carregarComboCulturas` → `OutrosManejos` → `Clima` → `Ufs` → `Portarias` → `Grupos` → `Solos`
  → `gerarRelatorioXLS`). O plano confirma isso.
- O grupo de cultivar e a classe de solo padrão da demo são grupo I e a classe que corresponde à
  água disponível escolhida na spec 004. O usuário pode trocar.
- A tabela de equivalência entre classe AD do ZARC e água disponível em mm fica na spec 004.
- O risco do ZARC é a probabilidade oficial de perda; o risco do TELLUS (spec 005) é outro número,
  e os dois aparecem lado a lado sem serem misturados.
