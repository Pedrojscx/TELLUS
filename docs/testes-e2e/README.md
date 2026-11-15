# Testes de ponta a ponta (Playwright)

Bateria auditável do TELLUS. Cada teste usa o site como o produtor usaria, no navegador de verdade, contra a API local.
Cada etapa tira uma **captura de tela** e registra **o que foi verificado, o esperado e o obtido**. No fim, tudo vira
o relatório [RELATORIO.md](RELATORIO.md), com o commit testado e as versões do navegador e da API.

## Como rodar

Na pasta `frontend`:

```
npm run test:e2e
```

- Usa o Microsoft Edge instalado no computador (`channel: "msedge"`); não baixa navegador.
- Se a API (porta 8000) e o site (porta 4321) já estiverem rodando, a bateria usa os dois. Se não, sobe os dois sozinha.
- Leva cerca de 1 minuto. Precisa das séries e caches versionados do repositório, sem login da NASA.
- Cada execução **apaga e regrava** `capturas/`, `evidencias/` e `RELATORIO.md`: o relatório sempre mostra uma
  execução só, inteira.
- Rastro detalhado de um teste que falhou: `npx playwright show-trace test-results/<pasta do teste>/trace.zip`.

## O que fica nesta pasta

| Caminho | Conteúdo |
|---|---|
| `RELATORIO.md` | Resumo, defeitos conhecidos e, para cada teste, as etapas com verificações e capturas. Gerado; não editar à mão. |
| `capturas/<suíte>/<teste>/NN-etapa.png` | Uma captura por etapa, numerada na ordem em que aconteceu. Uma verificação que falha gera também uma captura `FALHA`. |
| `evidencias/08-api/*.json` | Respostas completas da API usadas nas checagens do contrato (PT, EN, versões, erros). |

## Suítes

| Arquivo (`frontend/e2e/`) | O que cobre |
|---|---|
| `01-tela-inicial.e2e.ts` | Marca, passo a passo, busca de município, coordenadas, ponto fora do Brasil, fontes do local, ida à comparação. |
| `02-entradas.e2e.ts` | Entradas vazias, água disponível inválida, caso de referência válido, metodologia sem escolha. |
| `03-calculo-real.e2e.ts` | Caso de referência (Rio Verde-GO, colheita 20/01/2027, argilosa, grupo "não sei"): resultado real, alternativas ordenadas, riscos separados, 3 cenários, fontes, contextos que não entram no cálculo, nenhum texto de previsão. |
| `04-premissas.e2e.ts` | Padrões reais (Cepea, Conab), edição do preço do milho, cotação do sorgo (data futura recusada) e efeito no resultado. |
| `05-idioma.e2e.ts` | Seletor PT \| EN, idioma mantido entre telas, resultado real em inglês sem "(PT)" nem palavras portuguesas, volta ao PT, link `?lang=en`. |
| `06-celular.e2e.ts` | Fluxo completo em 390 × 844 com toque, sem rolagem lateral. |
| `07-erros-simulados.e2e.ts` | Simulação de sucesso, fonte com cópia guardada e falha sem cópia; os três estados de uma fonte. |
| `08-api.e2e.ts` | Mesmo pedido em PT e EN com números, ordem e hash idênticos; versões 1.1.0 aceita e 2.0.0 recusada; área não confirmada recusada. |

## Defeitos conhecidos

Um teste marcado com `test.fail` descreve o comportamento **correto** e falha enquanto o defeito existir. No
relatório ele aparece como "defeito conhecido (falhou como esperado)", com a captura do problema. Quando o defeito
for corrigido, o Playwright acusa "passou inesperadamente": é a hora de tirar a marca `test.fail`.

Histórico: a primeira execução (15/11/2026) encontrou dois defeitos com grupo "não sei", o caso de referência. A lista
de fontes da resposta vinha vazia (a tela mostrava ✕ em todas as culturas e o estado geral não detectava cópia
guardada) e o valor padrão da premissa editada vinha nulo ("sem padrão com fonte → 70"). Os dois foram corrigidos
no mesmo dia; os testes `Grupo "não sei": …` das suítes 03 e 04 ficaram como regressão.

## Como auditar

1. Confira no topo do relatório o commit testado e se havia alterações locais fora do commit.
2. Para cada teste, leia as verificações (esperado × obtido) e abra a captura da etapa.
3. Para o contrato da API, compare com os arquivos em `evidencias/08-api/`.
4. Para repetir, faça checkout do mesmo commit e rode `npm run test:e2e`.
