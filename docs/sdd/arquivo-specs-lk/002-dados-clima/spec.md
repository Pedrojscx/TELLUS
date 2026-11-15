# Feature Specification: Dados de clima do local

**Feature Branch**: `002-dados-clima`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "002-dados-clima: a partir do resultado de localização (001), obter a série diária histórica de clima do local: temperatura, radiação, umidade e vento do NASA POWER; chuva do IMERG Final (NASA GPM) com a estação INMET mais próxima como referência local; guardar tudo com procedência para uso offline; mostrar na tela de fontes a comparação das fontes de chuva. A chuva do POWER nunca entra no cálculo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Série histórica diária pronta para o motor hídrico (Priority: P1)

Depois de escolher o local, o sistema reúne, para cada dia do histórico, as variáveis que o motor
hídrico (spec 005) precisa: temperatura máxima e mínima, radiação solar, umidade relativa, vento
e chuva. Cada valor diário sabe de que fonte veio e se é válido.

**Why this priority**: sem clima não existe risco de falta de água nem cenário de produtividade.

**Independent Test**: para Rio Verde-GO, pedir a série e conferir que ela cobre os anos
esperados, que dias com valor de preenchimento (-999) aparecem como ausentes e que a chuva vem do
IMERG.

**Acceptance Scenarios**:

1. **Given** Rio Verde-GO resolvido pela 001, **When** a série é pedida, **Then** cada dia traz
   Tmax, Tmin, radiação, umidade e vento do POWER e chuva do IMERG, com a fonte de cada variável.
2. **Given** um dia com valor de preenchimento numa variável, **When** a série é montada, **Then**
   aquele valor fica marcado como ausente e nunca vira número no cálculo.
3. **Given** a série pronta, **When** se pergunta pela cobertura, **Then** o sistema informa por
   ano quantos dias válidos existem para cada variável.

---

### User Story 2 - Comparação das fontes de chuva na tela de fontes (Priority: P1)

O usuário (ou o júri) abre a tela de fontes e vê, para o local, como a chuva do IMERG, a da
estação INMET e a do POWER se comparam nos dias em que as três existem: totais, viés e erro médio.
Fica claro por que o TELLUS usa o IMERG e não o POWER.

**Why this priority**: é a prova de honestidade do produto (Princípios II e III) e responde ao
maior risco apontado pelo conselho.

**Independent Test**: para Rio Verde-GO, os números da comparação reproduzem os do
`docs/pesquisa_chuva/RELATORIO.md`.

**Acceptance Scenarios**:

1. **Given** Rio Verde-GO, **When** a comparação é feita em jan–jun dos anos conferidos, **Then**
   o total pareado dá INMET 6.349,60 mm, IMERG 6.284,47 mm (viés -1,03%) e POWER 4.637,61 mm
   (viés -26,96%) nas mesmas 1.218 datas, com tolerância de 0,1 mm.
2. **Given** uma estação a mais de 50 km (aviso da 001), **When** a comparação é mostrada, **Then**
   ela vem com o aviso de que a estação não representa bem o ponto.
3. **Given** um dia da estação com menos de 24 horas válidas, **When** a soma diária é feita,
   **Then** o dia fica fora da comparação e entra na contagem de excluídos.

---

### User Story 3 - Funcionar sem internet e sem credencial (Priority: P2)

Na demonstração a internet pode falhar. O sistema usa o que já está guardado e diz de quando são
os dados. Se faltar a credencial Earthdata para baixar o IMERG de um local novo, o sistema declara
a lacuna da chuva em vez de trocar por outra fonte em silêncio.

**Why this priority**: Princípio V; a demo não pode depender da rede.

**Independent Test**: desligar a rede e pedir Rio Verde-GO: a série completa volta, com a data dos
dados guardados.

**Acceptance Scenarios**:

1. **Given** dados guardados de Rio Verde-GO e sem internet, **When** a série é pedida, **Then** ela
   volta completa e a resposta informa a data em que cada fonte foi obtida.
2. **Given** um local novo, sem internet, **When** a série é pedida, **Then** o sistema responde com
   erro claro dizendo que aquele local ainda não foi baixado.
3. **Given** um local novo e sem credencial Earthdata, **When** a série é pedida, **Then** as
   variáveis do POWER vêm e a chuva vem marcada como indisponível, com o motivo.

---

### Edge Cases

- O IMERG Final tem atraso de meses; os últimos meses não existem. A série termina no último dia
  publicado e a resposta informa essa data.
- Respostas 404 para dias ainda não publicados não são erro; contam como "ainda não publicado".
- Anos com falhas: um ano com chuva faltando em dias da estação de cultivo é marcado como
  incompleto; a spec 005 decide se o usa.
- A célula do POWER pedida pelo ponto é diferente da célula do ponto antigo do REGISTRO (5 km de
  diferença, outra célula); vale sempre o ponto da 001.
- Mudança de versão da fonte (ex.: IMERG V07B): a versão fica gravada na procedência.
- Fuso: o dia é o dia UTC das fontes; a soma horária da estação segue a mesma convenção do
  RELATORIO (01h às 00h UTC).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST obter do NASA POWER, para o ponto da 001, a série diária de
  temperatura máxima, temperatura mínima, radiação solar de onda curta, umidade relativa e
  velocidade do vento a 2 m, desde 1984-01-01 até o último dia disponível.
- **FR-002**: O sistema MUST obter a chuva diária do IMERG Final (GPM, versão vigente) para a
  célula da 001, desde o início da série (junho de 2000) até o último dia publicado.
- **FR-003**: O sistema MUST obter a chuva horária da estação INMET indicada pela 001 e somá-la por
  dia, exigindo 24 horas válidas para o dia contar.
- **FR-004**: A chuva do POWER MUST ser obtida só para a comparação de fontes e MUST NOT ser
  entregue como chuva para cálculo (Princípio III).
- **FR-005**: Valores de preenchimento (-999 e equivalentes de cada fonte) MUST virar ausência e
  ser contados por variável e por ano.
- **FR-006**: Cada valor entregue MUST carregar a fonte, a versão do produto, a data de obtenção e a
  unidade (Princípio I).
- **FR-007**: Toda resposta original das fontes MUST ser guardada localmente com sua procedência
  (endereço, parâmetros, data), e uma segunda consulta igual MUST usar o guardado.
- **FR-008**: Sem acesso à fonte, o sistema MUST responder com os dados guardados e informar a data
  deles; sem dados guardados, MUST responder com erro claro.
- **FR-009**: A credencial Earthdata MUST ser lida da configuração local, nunca exibida nem gravada
  em log ou na procedência (Princípio VII).
- **FR-010**: O sistema MUST calcular, nos dias em que as fontes coexistem, total, viés percentual,
  erro absoluto médio e raiz do erro quadrático médio de IMERG e POWER contra a estação, e a fração
  de dias com chuva ≥ 1 mm de cada fonte.
- **FR-011**: A comparação MUST permitir recorte por período (ano, meses) e informar quantos dias
  entraram e quantos foram excluídos, com o motivo.
- **FR-012**: O sistema MUST informar, por ano, a cobertura de cada variável e o último dia
  disponível de cada fonte.
- **FR-013**: Rio Verde-GO MUST ter os dados guardados no repositório da demo (fora do Git, com
  procedência no Git), de modo que a demonstração funcione na primeira execução sem rede.

### Key Entities

- **Série diária**: local, data, valores por variável, fonte de cada valor, marca de ausente.
- **Procedência**: fonte, produto e versão, endereço consultado, parâmetros, data de obtenção,
  arquivo guardado.
- **Cobertura**: por ano e variável, dias válidos, dias ausentes, último dia disponível.
- **Comparação de chuva**: período, dias pareados, dias excluídos com motivo, totais e métricas por
  fonte contra a estação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para Rio Verde-GO, a comparação de jan–jun reproduz os totais do RELATORIO.md com
  tolerância de 0,1 mm.
- **SC-002**: Nenhum valor de preenchimento chega ao cálculo em 100% dos testes com dias sujos
  conhecidos.
- **SC-003**: Sem internet, Rio Verde-GO resolve a série completa em menos de 5 segundos.
- **SC-004**: Um local novo, com internet e credencial, tem a série completa obtida em menos de 10
  minutos na primeira vez.
- **SC-005**: 100% dos valores entregues têm fonte, versão e data de obtenção.

## Assumptions

- Recorte IMERG já validado: coleção diária GPM_3IMERGDF V07/V07B, acesso autenticado
  oficial funcionando; o caminho que funcionou está no REGISTRO.md (DAP4 `.dap.nc4`).
- A credencial é o `EARTHDATA_TOKEN` do `.env`, já com a aplicação GES DISC autorizada.
- O IMERG é usado na célula, sem correção pela estação; o viés local é mostrado, não aplicado.
- A estação de comparação é a indicada pela 001; estações vizinhas extras ficam fora desta spec.
- Período mínimo útil para o motor: anos com IMERG completo na estação de cultivo da 2ª safra
  (janeiro a julho).
- ERA5 (Open-Meteo) não é fonte deste produto; aparece só como registro histórico da pesquisa.
- Os scripts da pesquisa (`scripts/chuva_*.py`) servem de referência e de caso de teste, não de
  produto.
