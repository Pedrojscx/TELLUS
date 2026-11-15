# Feature Specification: Localização e referências do local

**Feature Branch**: `001-localizacao`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "001-localizacao: o usuário escolhe um local em qualquer ponto do Brasil (clicando no mapa, digitando lat/lon ou buscando um município). O sistema resolve esse local para tudo o que as specs seguintes precisam: município e UF com código IBGE (para ZARC e Conab), célula do NASA POWER, célula do IMERG, estação INMET mais próxima com distância e altitude, e a praça Conab mais próxima. Cada resolução traz fonte e distância, e avisa quando a referência fica longe ou não existe. Rio Verde-GO é o local padrão da demonstração e o caso de validação (estação A025 em -17.785,-50.965; células POWER e IMERG já conferidas no registro da equipe). Fora do Brasil é recusado com mensagem clara."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher o local da lavoura (Priority: P1)

O produtor ou técnico abre o TELLUS e indica onde fica a lavoura. Pode buscar o município pelo
nome, digitar latitude e longitude ou clicar no mapa. O sistema confirma o local escolhido
(município, UF e coordenadas) antes de seguir para a decisão da segunda safra.

**Why this priority**: sem local não há clima, ZARC nem custo. É a porta de entrada do fluxo
único (Princípio VI).

**Independent Test**: informar "Rio Verde" na busca, escolher Rio Verde-GO e ver o município,
a UF, o código IBGE e as coordenadas do ponto confirmados.

**Acceptance Scenarios**:

1. **Given** a tela inicial, **When** o usuário não informa nada, **Then** o local padrão
   Rio Verde-GO já aparece selecionado e identificado como local da demonstração.
2. **Given** a busca por município, **When** o usuário digita "rio verde", **Then** aparecem as
   opções que combinam com o texto, com UF (ex.: Rio Verde-GO e Rio Verde de Mato Grosso-MS), e a
   escolha de uma delas define o ponto.
3. **Given** a entrada de coordenadas, **When** o usuário digita -17.785, -50.965, **Then** o
   sistema identifica o município Rio Verde-GO a partir do ponto.
4. **Given** o mapa, **When** o usuário clica num ponto do território brasileiro, **Then** o
   ponto vira o local escolhido e o município correspondente é mostrado.

---

### User Story 2 - Ver as referências de dados do local e a distância de cada uma (Priority: P1)

Depois de escolher o local, o usuário vê, numa lista curta, de onde vêm os dados que o TELLUS vai
usar para aquele ponto: a célula de grade do NASA POWER, a célula do IMERG, a estação INMET mais
próxima, a praça de custos Conab mais próxima e o município usado para o ZARC. Cada item mostra a
fonte e a distância até o ponto escolhido.

**Why this priority**: os Princípios I, II e a regra de cobertura da constituição exigem dizer
qual referência foi usada e a que distância. As specs 002 (clima), 003 (ZARC) e 006 (economia)
dependem dessas referências.

**Independent Test**: escolher Rio Verde-GO e conferir as referências contra os valores já
registrados (estação A025 a cerca de 4 km do ponto da estação; células POWER e IMERG com os
centros conferidos no registro da equipe).

**Acceptance Scenarios**:

1. **Given** Rio Verde-GO escolhido, **When** as referências são resolvidas, **Then** aparecem a
   estação INMET A025 (com distância e altitude), a célula POWER e a célula IMERG (com o centro de
   cada uma e a distância até o ponto), a praça Conab Rio Verde-GO e o município de Rio Verde
   (código IBGE) para o ZARC.
2. **Given** um ponto cuja estação INMET mais próxima fica além do limite de distância, **When** as
   referências são resolvidas, **Then** a estação aparece com aviso de que está longe e de que a
   comparação local de chuva perde validade.
3. **Given** um município sem praça Conab, **When** as referências são resolvidas, **Then** a praça
   mais próxima aparece com a distância e o aviso de que os custos são de outra região.

---

### User Story 3 - Recusa clara fora do Brasil ou em ponto inválido (Priority: P2)

Se o usuário escolhe um ponto fora do território brasileiro, no mar, ou digita coordenadas
inválidas, o sistema explica o problema e mantém o local anterior.

**Why this priority**: evita respostas sem sentido, mas não bloqueia a demonstração.

**Independent Test**: digitar 40.71, -74.00 (Nova York) e ver a recusa com mensagem; o local
anterior continua selecionado.

**Acceptance Scenarios**:

1. **Given** coordenadas fora do Brasil, **When** o usuário confirma, **Then** aparece "O TELLUS
   cobre apenas o território brasileiro" e o local anterior é mantido.
2. **Given** latitude fora de -90 a 90 ou longitude fora de -180 a 180, ou texto não numérico,
   **When** o usuário confirma, **Then** o campo é marcado como inválido, com o motivo.
3. **Given** um ponto no oceano dentro da faixa costeira, **When** o usuário confirma, **Then** o
   sistema informa que o ponto não está em município brasileiro.

---

### Edge Cases

- Ponto exatamente na divisa entre municípios ou estados: vale o município que contém o ponto; se
  a resolução for ambígua, o sistema escolhe um e mostra o vizinho como alternativa.
- Município com nome repetido em várias UFs (ex.: "Santa Helena"): a busca sempre mostra a UF.
- Busca sem acento ou com grafia parcial ("goiania", "rio ver") encontra o município.
- Ponto na borda entre duas células de grade: vale a célula que a fonte devolve para aquelas
  coordenadas; o centro devolvido é registrado.
- Estação INMET desativada ou sem dados recentes: não conta como a mais próxima para chuva; a
  próxima ativa é usada e o motivo é mostrado.
- Fonte de referência fora do ar: usa a última resolução guardada e informa a data (Princípio V).
- Ilhas oceânicas brasileiras (ex.: Fernando de Noronha): aceitas como Brasil, com aviso de que
  podem faltar estação, ZARC e praça Conab.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar o local por três meios: busca de município por nome, entrada
  de latitude/longitude em graus decimais e clique no mapa.
- **FR-002**: O sistema MUST iniciar com Rio Verde-GO selecionado como local padrão da
  demonstração.
- **FR-003**: O sistema MUST recusar pontos fora do território brasileiro e coordenadas inválidas,
  com mensagem que diga o motivo, sem perder o local anterior.
- **FR-004**: Para todo local aceito, o sistema MUST identificar município, UF e código IBGE de 7
  dígitos, e informar a fonte da malha municipal usada.
- **FR-005**: A busca de município MUST ignorar acentos e maiúsculas, aceitar texto parcial e
  mostrar sempre a UF de cada opção.
- **FR-006**: O sistema MUST resolver a célula do NASA POWER que contém o ponto e informar o centro
  da célula e a distância em km até o ponto.
- **FR-007**: O sistema MUST resolver a célula do IMERG (0,1°) que contém o ponto e informar o
  centro e a distância em km até o ponto.
- **FR-008**: O sistema MUST encontrar a estação automática INMET ativa mais próxima e informar
  código, nome, coordenadas, altitude e distância em km até o ponto.
- **FR-009**: O sistema MUST encontrar a praça de custos Conab mais próxima entre as que têm
  planilha de custo publicada e informar nome, UF, culturas disponíveis e distância em km.
- **FR-010**: Cada referência resolvida MUST trazer fonte, data de obtenção e distância
  (Princípio I).
- **FR-011**: O sistema MUST emitir aviso quando a estação INMET ficar a mais de 50 km do ponto
  ou quando a praça Conab ficar em outro município, e MUST declarar a lacuna quando uma referência
  não existir. Nenhuma referência é preenchida em silêncio.
- **FR-012**: O resultado da localização MUST ficar disponível às demais specs como um único
  conjunto de dados do local (ponto, município, células e referências, cada uma com fonte e
  aviso).
- **FR-013**: O mesmo ponto MUST produzir sempre o mesmo resultado de localização, enquanto as
  fontes não mudarem (Princípio IV).
- **FR-014**: Com as fontes fora do ar, o sistema MUST funcionar para locais já resolvidos antes
  e para Rio Verde-GO, usando os dados guardados e informando a data deles (Princípio V).
- **FR-015**: Para Rio Verde-GO, o resultado MUST coincidir com os valores conferidos no
  registro da equipe: estação A025 (-17,785; -50,965; 780 m), centro IMERG (-17,75; -50,95) e centro POWER
  da célula que contém a estação (-18; -51,25), com tolerância de 0,01° nas coordenadas.

### Key Entities

- **Local escolhido**: ponto (latitude, longitude), meio de escolha (busca, coordenadas, mapa),
  município, UF, código IBGE.
- **Referência de dados**: tipo (célula POWER, célula IMERG, estação INMET, praça Conab, município
  ZARC), identificador, coordenadas, distância até o ponto, fonte, data de obtenção, avisos.
- **Estação INMET**: código, nome, coordenadas, altitude, situação (ativa ou não), início da
  série.
- **Praça Conab**: nome, UF, coordenadas de referência (sede do município), culturas e safras com
  planilha de custo.
- **Resultado de localização**: o local escolhido mais a lista de referências e os avisos. É a
  entrada das specs 002, 003 e 006.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O usuário define o local da lavoura em menos de 30 segundos por qualquer um dos três
  meios.
- **SC-002**: Para Rio Verde-GO, 100% das referências conferem com os valores do registro da equipe
  (FR-015).
- **SC-003**: Num conjunto de teste com 10 pontos conhecidos (capitais de UF e Rio Verde-GO), o
  município identificado está correto em 10 de 10.
- **SC-004**: 100% das referências exibidas mostram fonte e distância; nenhuma aparece sem isso.
- **SC-005**: Pontos fora do Brasil e coordenadas inválidas são recusados em 100% dos casos de
  teste, com mensagem.
- **SC-006**: Sem internet, Rio Verde-GO resolve por completo e a tela informa a data dos dados
  guardados.

## Assumptions

- Malha municipal e códigos: IBGE (malha e lista de municípios oficiais). Coordenadas em graus
  decimais, datum WGS84/SIRGAS 2000, tratados como equivalentes nessa escala.
- Distâncias são em linha reta sobre a superfície da Terra (grande círculo), em km.
- A célula do POWER é a que a própria fonte devolve para o ponto. O registro da equipe mostra centros em
  passos de 0,5° de latitude e 0,625° de longitude; a spec 002 confirma isso na fonte.
- O limite de 50 km para a estação INMET é um valor inicial marcado como hipótese, editável. Ele
  vem da comparação de chuva grade × estação, que só faz sentido com a estação perto.
- A lista de praças Conab vem das planilhas de custo de produção publicadas pela Conab. A praça é
  localizada pela sede do município.
- Para o ZARC, o município do ponto é a referência; a disponibilidade das janelas por cultura é
  responsabilidade da spec 003.
- A escolha de local não exige login nem guarda dados pessoais.
- O mapa precisa de internet para as imagens de fundo; sem internet, a busca e as coordenadas
  continuam funcionando (FR-014).
- Fora de escopo: talhão, desenho de área, endereço de rua, várias lavouras ao mesmo tempo.
