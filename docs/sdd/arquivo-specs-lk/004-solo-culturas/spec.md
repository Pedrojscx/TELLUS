# Feature Specification: Parâmetros de solo e culturas

**Feature Branch**: `004-solo-culturas`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "004-solo-culturas: reunir, com fonte, data e unidade, os parâmetros agronômicos que o motor hídrico usa: água disponível do solo (ligada às classes AD do ZARC), Kc por fase, duração das fases, profundidade de raiz, fração de esgotamento e Ky de milho 2ª safra, sorgo granífero e da planta de cobertura. Sem fonte, o valor é hipótese editável."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parâmetros de cada cultura com fonte visível (Priority: P1)

O motor hídrico (spec 005) pede os parâmetros de uma cultura e recebe cada número com fonte, data
e unidade. O usuário vê na tela de premissas de onde veio cada Kc, cada duração de fase e cada Ky,
e quais são hipóteses.

**Why this priority**: Princípio I. O conselho apontou números sem fonte como o maior risco; a
revisão agronômica pedida (Kc, Ky, fases) começa aqui.

**Independent Test**: pedir os parâmetros do milho 2ª safra e verificar que todos os campos têm
fonte ou a marca de hipótese, e que nenhum valor está escrito no código.

**Acceptance Scenarios**:

1. **Given** a cultura milho 2ª safra, **When** os parâmetros são pedidos, **Then** vêm Kc inicial,
   médio e final, duração das quatro fases (inicial, desenvolvimento, média, final), profundidade
   máxima de raiz, fração de esgotamento p e Ky (total e por fase), cada um com fonte e unidade.
2. **Given** um parâmetro sem fonte publicada, **When** exibido, **Then** aparece marcado como
   hipótese e editável.
3. **Given** um parâmetro editado pelo usuário, **When** usado no cálculo, **Then** a resposta
   mostra que o valor foi alterado e qual era o original.

---

### User Story 2 - Água disponível do solo coerente com o ZARC (Priority: P1)

O usuário escolhe o tipo de solo de duas formas: pela classe de água disponível do ZARC (AD1 a AD6)
ou digitando a água disponível em mm. O sistema mantém as duas coerentes, para que o ZARC (spec
003) e o motor hídrico (spec 005) falem do mesmo solo.

**Why this priority**: a água disponível é a entrada do produtor mais sensível no balanço hídrico,
e o ZARC já classifica os solos assim.

**Independent Test**: escolher AD4 e ver o valor em mm usado no balanço e a faixa oficial da
classe; digitar um valor em mm e ver a classe AD correspondente.

**Acceptance Scenarios**:

1. **Given** a escolha da classe AD4, **When** o balanço for calculado, **Then** usa o valor
   representativo da classe em mm, com a fonte da faixa.
2. **Given** um valor digitado em mm, **When** confirmado, **Then** o sistema mostra a classe AD a
   que ele pertence, usada na consulta do ZARC.
3. **Given** um valor fora das faixas publicadas, **When** digitado, **Then** é aceito com aviso de
   que fica fora das classes do ZARC.

---

### User Story 3 - Revisar e corrigir parâmetros sem mexer em código (Priority: P2)

Um agrônomo da equipe (ou mentor do hackathon) revisa os parâmetros e corrige um valor ou uma
fonte num único arquivo de referência legível, e o sistema passa a usar o valor novo.

**Why this priority**: viabiliza a revisão agronômica pedida pelo conselho dentro do prazo.

**Independent Test**: alterar o Ky do sorgo no arquivo de referência e ver o novo valor na
resposta, com a fonte atualizada.

**Acceptance Scenarios**:

1. **Given** o arquivo de referência, **When** um valor é corrigido, **Then** a próxima consulta
   devolve o valor novo com a fonte nova.
2. **Given** um parâmetro sem fonte nem marca de hipótese, **When** o sistema é verificado, **Then**
   a verificação falha e aponta o campo.

---

### Edge Cases

- Fontes diferentes para o mesmo parâmetro (ex.: FAO-56 e Embrapa): a referência guarda a escolhida
  e cita a alternativa.
- Duração das fases depende do ciclo (grupo de cultivar I, II, III); a referência traz durações
  por grupo, coerentes com os grupos do ZARC.
- Kc da planta de cobertura pode não ter tabela FAO direta; usa-se a cultura análoga declarada,
  marcada como hipótese.
- Ky por fase versus Ky total: o motor usa o que estiver disponível com fonte; se só houver o
  total, a resposta informa isso.
- Unidades: Kc adimensional, fases em dias, raiz em m, água disponível em mm (na zona radicular)
  e mm/cm de solo quando vier por textura.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST manter, para milho 2ª safra, sorgo granífero 2ª safra e a planta de
  cobertura, os parâmetros: Kc inicial, médio e final; duração das fases inicial, desenvolvimento,
  média e final por grupo de cultivar; profundidade inicial e máxima de raiz; fração de
  esgotamento p; Ky total e, quando houver, Ky por fase.
- **FR-002**: Todo parâmetro MUST ter valor, unidade, fonte (referência bibliográfica ou portaria
  com página ou tabela), data de consulta e status (`fonte` ou `hipotese`).
- **FR-003**: Os parâmetros MUST ficar em arquivos de referência versionados e legíveis, nunca
  escritos no código (Princípio I).
- **FR-004**: Uma verificação automática MUST falhar se algum parâmetro estiver sem fonte e sem a
  marca de hipótese.
- **FR-005**: O sistema MUST manter a tabela de classes AD do ZARC (AD1 a AD6) com a faixa de água
  disponível de cada uma, a fonte e o valor representativo usado no balanço.
- **FR-006**: O sistema MUST aceitar a água disponível por classe AD ou por valor em mm, convertendo
  um no outro.
- **FR-007**: O usuário MUST poder editar qualquer parâmetro para uma simulação, e a resposta MUST
  indicar os valores alterados e os originais.
- **FR-008**: A planta de cobertura padrão MUST ser a braquiária solteira (*Urochloa ruziziensis*),
  com o ZARC de milho com braquiária como referência oficial mais próxima e o aviso correspondente
  (decisão de 14/11).
- **FR-009**: O sistema MUST declarar, para cada cultura, qual cultura análoga foi usada quando o
  parâmetro não existe para ela.

### Key Entities

- **Parâmetro**: nome, cultura, grupo de cultivar (quando couber), valor, unidade, fonte, data de
  consulta, status, alternativa citada.
- **Cultura**: nome, uso (grão ou cobertura), grupos de cultivar, conjunto de parâmetros.
- **Classe de água disponível**: código AD, faixa em mm, valor representativo, fonte.
- **Premissas da simulação**: parâmetros efetivamente usados, com marca de editado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos parâmetros têm fonte ou marca de hipótese (verificação automática).
- **SC-002**: Pelo menos 80% dos parâmetros de milho e sorgo têm fonte publicada (não hipótese).
- **SC-003**: Um revisor corrige um parâmetro em menos de 2 minutos, editando só o arquivo de
  referência.
- **SC-004**: A conversão classe AD ↔ mm é coerente nos dois sentidos para 100% das classes.

## Assumptions

- Fontes iniciais: FAO-56 (Allen et al., 1998) para Kc, fases, raiz e p; FAO-33 (Doorenbos e
  Kassam, 1979) e FAO-66 para Ky; portaria/notas técnicas do ZARC para as classes AD; Embrapa
  Milho e Sorgo para ajustes ao Cerrado. A busca das tabelas exatas é tarefa do plano.
- Durações FAO-56 para regiões tropicais são ajustadas por grupo de cultivar do ZARC; o ajuste sem
  fonte fica como hipótese.
- A soja não precisa de parâmetros aqui: só a data de colheita dela entra no fluxo.
- Não há medição de solo do talhão; a água disponível vem da escolha do usuário (Princípio II).
