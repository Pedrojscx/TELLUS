# Feature Specification: Versão em inglês (site e sistema)

**Feature Branch**: `014-idioma-ingles`  
**Created**: 2026-11-15  
**Status**: Draft

**Input**: Versão do site e do sistema inteiro em inglês, com a troca de idioma fácil no topo do site.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trocar o idioma no topo (Priority: P1)

Como avaliador ou produtor que não lê português, quero trocar o site para inglês com um clique no topo da página.

**Why this priority**: Os juízes do Space Apps são internacionais. Sem isso, eles não conseguem usar o fluxo.

**Independent Test**: Abrir qualquer tela, clicar em "EN" no topo e conferir que a mesma tela aparece em inglês. Navegar até o resultado sem voltar ao português.

**Acceptance Scenarios**:

1. **Given** qualquer tela em português, **When** clico em "EN" no seletor do topo, **Then** a mesma tela aparece em inglês, sem perder o que já preenchi (lavoura, entradas, premissas).
2. **Given** que escolhi inglês, **When** navego para outra tela ou recarrego a página, **Then** o site continua em inglês.
3. **Given** um link com `?lang=en`, **When** o abro num navegador novo, **Then** o site já abre em inglês.

---

### User Story 2 - Resultado e mensagens do sistema em inglês (Priority: P1)

Como usuário em inglês, quero que o resultado, os avisos, os erros, as hipóteses e os motivos de indisponibilidade venham em inglês, não só os rótulos das telas.

**Why this priority**: Boa parte do texto que o usuário lê vem do backend (contrato 1.1.0). Traduzir só os botões deixa o resultado em português.

**Independent Test**: Rodar o caso de referência (Rio Verde-GO, colheita 20/01/2027, argilosa, grupo "não sei") em inglês. Nenhuma frase em português pode aparecer no resultado, exceto nomes próprios de fontes e de normas.

**Acceptance Scenarios**:

1. **Given** idioma inglês, **When** calculo o caso de referência, **Then** alternativas, critério de ordem, avisos, hipóteses, "o que foi consultado" e contextos opcionais aparecem em inglês.
2. **Given** idioma inglês e uma fonte indisponível, **When** o erro aparece, **Then** a mensagem, a origem e a ação sugerida estão em inglês, e a data do cache segue o formato do idioma.
3. **Given** uma mensagem do backend ainda sem tradução, **When** ela aparece em inglês, **Then** o texto em português é mostrado com a marca "(PT)", e nunca um texto vazio ou um código cru.

---

### User Story 3 - Documentação de entrega em inglês (Priority: P2)

Como avaliador, quero ler o README, a explicação da metodologia e as fontes em inglês.

**Independent Test**: Abrir o README pelo GitHub e encontrar a versão em inglês linkada no topo.

**Acceptance Scenarios**:

1. **Given** o repositório, **When** abro o README, **Then** há um link para `README.en.md` com o mesmo conteúdo essencial (o que é, como rodar, fontes, limitações).

### Edge Cases

- Números e unidades: em inglês, separador decimal é ponto e milhar é vírgula (R$ 5,889.09/ha). A unidade e a moeda NÃO são convertidas: continuam R$, sc de 60 kg, mm e ha.
- Datas: em inglês, usar formato sem ambiguidade (ex.: "Jan 20, 2027"). Nunca "01/20" contra "20/01" sem o mês por extenso.
- Termos oficiais brasileiros (ZARC, Conab, CEPEA, INMET, CAR, decêndio) ficam com o nome original e uma explicação curta na primeira vez ("ZARC, Brazil's official agricultural climate risk zoning").
- O texto em inglês também não pode chamar risco histórico de previsão. Palavras proibidas em inglês: "forecast", "will rain", "predicted yield", "guaranteed".
- Código de erro, código de aviso e valores do contrato (ex.: `milho_2a_safra`, `final_com_cache`) não mudam com o idioma. Só o texto legível muda.
- O seletor de idioma não pode depender só de cor ou bandeira: usar o texto "PT" e "EN", com o idioma atual marcado.
- Sem JavaScript, o site abre em português (padrão) e continua funcional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O site MUST ter um seletor de idioma PT | EN no cabeçalho de todas as telas (tela inicial e layout da comparação), visível no computador e no celular.
- **FR-002**: A escolha MUST ficar guardada no navegador e valer para todas as telas. `?lang=en` ou `?lang=pt` na URL MUST ter prioridade sobre o que está guardado.
- **FR-003**: O atributo `lang` do `<html>` MUST acompanhar o idioma (`pt-BR` ou `en`).
- **FR-004**: Todo texto fixo do frontend MUST sair de um dicionário por idioma (`pt`, `en`) com as mesmas chaves. Um teste MUST falhar se uma chave existir num idioma e faltar no outro.
- **FR-005**: O pedido do contrato MUST aceitar um campo opcional `idioma` (`pt-BR` padrão, `en`). As demais rotas da API MUST aceitar o cabeçalho `Accept-Language`. Mudança aditiva: contrato passa a 1.2.0 e continua aceitando pedidos 1.1.0.
- **FR-006**: O backend MUST traduzir as mensagens pelo código (aviso, erro, motivo, hipótese, critério de ordem) a partir de um catálogo versionado por idioma. Mensagem com valores variáveis MUST usar modelo com campos nomeados (ex.: `{estacao}`, `{distancia_km}`).
- **FR-007**: Mensagem sem tradução MUST cair no português com a marca "(PT)" e MUST ser listada por um teste de cobertura do catálogo.
- **FR-008**: Números, moedas e datas MUST ser formatados pelo idioma ativo no frontend. Os valores numéricos da resposta da API MUST continuar iguais nos dois idiomas.
- **FR-009**: O resultado do mesmo pedido em `pt-BR` e em `en` MUST ter as mesmas alternativas, a mesma ordem e os mesmos números. Só o texto muda.
- **FR-010**: O guia de marca MUST ganhar a lista de tom e palavras proibidas em inglês.
- **FR-011**: O repositório MUST ter `README.en.md`, linkado no topo do `README.md`.

### Key Entities

- **Dicionário do frontend**: chave → texto, um arquivo por idioma.
- **Catálogo de mensagens do backend**: código → modelo de texto por idioma, com os campos variáveis.
- **Idioma ativo**: `pt-BR` ou `en`. Vem da URL, do navegador ou do padrão, nesta ordem.

## Success Criteria *(mandatory)*

- **SC-001**: Com o idioma em inglês, o caso de referência roda do início ao resultado sem nenhuma frase em português na tela, fora nomes próprios. Conferido por teste automático do texto renderizado e pelo roteiro manual.
- **SC-002**: Trocar o idioma leva 1 clique em qualquer tela, e a escolha vale depois de recarregar a página.
- **SC-003**: 100% das chaves do dicionário do frontend e 100% dos códigos de mensagem do backend têm texto nos dois idiomas, ou aparecem no relatório de faltantes do teste.
- **SC-004**: O mesmo pedido em PT e em EN dá respostas com números e ordem idênticos (teste de igualdade ignorando os campos de texto).

## Assumptions

- Só dois idiomas: português (padrão) e inglês. Espanhol fica fora.
- Sem tradução automática em tempo real: todos os textos são escritos e revisados pela equipe.
- Os dados das fontes (nomes de estação, municípios, portarias do ZARC) ficam no original.
- A implementação NÃO entra na entrega de 15/11/2026 12h. A spec foi aberta às 10h20, depois do congelamento das 08h (docs/PLANO.md). Ela é trabalho para depois da entrega, salvo decisão contrária da equipe.
