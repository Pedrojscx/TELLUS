# Feature Specification: Comparação das três opções e recomendação

**Feature Branch**: `007-recomendacao`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "007-recomendacao: juntar ZARC (003), risco hídrico (005) e margem (006) numa comparação lado a lado de milho 2ª safra, sorgo e cobertura para a data de colheita da soja informada; ordenar as opções por uma regra transparente, explicar o porquê em texto simples e mostrar como a escolha muda conforme a data de colheita."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Três opções lado a lado (Priority: P1)

O produtor informa local e data de colheita da soja e vê milho, sorgo e cobertura lado a lado: a
janela e o risco do ZARC, o risco de falta de água do TELLUS, a margem nos três cenários e as
fontes. É a tela central da demonstração.

**Why this priority**: é o "fluxo único" da constituição e a versão mais forte que o conselho
enxergou.

**Independent Test**: Rio Verde-GO, colheita em 05/02, AD4, grupo I: as três opções aparecem
completas, com ZARC, risco, margem e fontes.

**Acceptance Scenarios**:

1. **Given** local, data de colheita e solo, **When** a comparação é pedida, **Then** cada opção
   mostra data de plantio, situação no ZARC (risco oficial ou fora da janela ou lacuna), chance de
   perda severa, margem conservadora, central e favorável, e avisos.
2. **Given** uma opção fora da janela do ZARC, **When** exibida, **Then** aparece destacada com o
   aviso de que fica sem crédito e seguro rural oficiais, mesmo que a margem seja boa.
3. **Given** qualquer número na comparação, **When** o usuário pede a fonte, **Then** vê fonte e
   data (Princípio I).

---

### User Story 2 - Ordem transparente e explicação em texto simples (Priority: P1)

O TELLUS ordena as três opções por uma regra pública e escreve, em duas ou três frases, por que a
primeira ficou em primeiro, usando os números da tela. Não há caixa-preta nem IA gerando texto.

**Why this priority**: o produtor e o técnico precisam entender e contestar a sugestão; texto vago
derruba a confiança.

**Independent Test**: num caso em que o sorgo tem margem central maior e risco menor que o milho,
a explicação cita a diferença de margem e de risco com os valores exibidos.

**Acceptance Scenarios**:

1. **Given** as três opções, **When** ordenadas, **Then** a regra é: primeiro as opções dentro da
   janela do ZARC; entre elas, maior margem no cenário conservador; empate decidido pela menor
   chance de perda severa.
2. **Given** a ordem, **When** a explicação é gerada, **Then** ela vem de um modelo de frase fixo
   preenchido com os números da tela, e diz que é estimativa regional, não previsão.
3. **Given** nenhuma opção de grão dentro da janela, **When** ordenadas, **Then** a cobertura é a
   sugerida e a explicação diz por quê.

---

### User Story 3 - Como a escolha muda com a data de colheita (Priority: P2)

O usuário vê uma linha do tempo de datas de colheita (por exemplo, de 1º de janeiro a 31 de março)
com a opção sugerida em cada data. Fica visível o ponto em que o milho deixa de compensar e o sorgo
ou a cobertura passam a ser melhores.

**Why this priority**: mostra o caso em que a margem muda a decisão em relação ao ZARC sozinho
(condição do conselho), mas a tela central funciona sem ela.

**Independent Test**: em Rio Verde-GO, a linha do tempo mostra pelo menos uma troca de opção
sugerida entre janeiro e março.

**Acceptance Scenarios**:

1. **Given** um local e um solo, **When** a linha do tempo é pedida, **Then** cada decêndio de
   colheita entre 1º/jan e 31/mar mostra a opção sugerida e a margem conservadora das três.
2. **Given** uma data em que o ZARC ainda permite o milho mas a margem conservadora do sorgo é
   maior, **When** exibida, **Then** ela é marcada como "aqui a margem muda a decisão".

---

### Edge Cases

- Dados incompletos numa opção (ex.: sem ZARC publicado para sorgo no município): a opção aparece
  com a lacuna declarada e fica depois das que têm dados completos.
- Margens iguais ao centavo e riscos iguais: ordem alfabética, declarada.
- Premissas editadas pelo usuário: a comparação mostra "com suas premissas" e permite voltar às
  originais.
- Amostra pequena de anos (aviso da 005): o aviso aparece no topo da comparação.
- Praça Conab distante ou estação INMET distante (avisos da 001): aparecem no topo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST montar, para local, data de colheita, solo e grupo de cultivar, a
  comparação das três opções com: data de plantio, situação no ZARC com portaria, chance de perda
  severa, déficit mediano, margem nos três cenários e avisos.
- **FR-002**: O sistema MUST ordenar as opções pela regra pública: dentro da janela do ZARC primeiro;
  depois maior margem conservadora; depois menor chance de perda severa; depois ordem alfabética.
- **FR-003**: A regra de ordenação MUST aparecer na tela, em texto, junto da ordem.
- **FR-004**: O sistema MUST gerar a explicação por modelo de frase fixo, preenchido com os números
  exibidos, sem geração por IA (fora do escopo do plano histórico).
- **FR-005**: Toda comparação MUST trazer a mensagem de que é estimativa regional em faixas, baseada
  em frequência histórica, e não previsão nem recomendação para o talhão (Princípio II).
- **FR-006**: O sistema MUST juntar no topo os avisos vindos das specs 001 a 006.
- **FR-007**: O sistema MUST calcular a linha do tempo de colheita por decêndio, de 1º/jan a 31/mar,
  com a opção sugerida e as margens conservadoras.
- **FR-008**: O sistema MUST marcar os decêndios em que a opção sugerida pela margem difere da
  opção de menor risco ZARC.
- **FR-009**: A comparação MUST ser determinística para o mesmo pedido (Princípio IV).
- **FR-010**: Rio Verde-GO, colheita em 05/02, AD4, grupo I, MUST ser o caso de demonstração
  padrão, com os dados guardados para rodar sem rede.

### Key Entities

- **Pedido de comparação**: local, data de colheita da soja, solo, grupo de cultivar, premissas
  editadas.
- **Opção**: cultura, data de plantio, situação ZARC, risco hídrico, margens por cenário, avisos,
  posição na ordem.
- **Explicação**: modelo de frase usado, valores preenchidos, texto final.
- **Linha do tempo**: por decêndio de colheita, opção sugerida, margens conservadoras, marca de
  mudança de decisão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A comparação completa do caso padrão aparece em menos de 3 segundos com dados
  guardados.
- **SC-002**: Um avaliador entende, só pela tela, por que a primeira opção foi sugerida (teste com
  pelo menos uma pessoa de fora da equipe, anotado no REGISTRO).
- **SC-003**: A linha do tempo de Rio Verde-GO mostra pelo menos um decêndio em que a margem muda a
  decisão em relação ao ZARC.
- **SC-004**: 100% das comparações trazem a mensagem de estimativa regional e os avisos das specs
  anteriores.

## Assumptions

- O critério "margem conservadora" foi escolhido para não premiar opções arriscadas com cenário
  favorável bom; é decisão de produto, registrada aqui e revisável.
- A situação no ZARC usa o grupo de cultivar e a classe de solo escolhidos (padrão grupo I e a
  classe AD da água disponível).
- O formato visual (cards, tabela, gráfico) fica para as specs 009 e 010; esta spec define o
  conteúdo e as regras.
- O contrato de dados entre esta comparação e a interface é definido na spec 008.
