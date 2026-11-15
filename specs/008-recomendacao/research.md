# Research: 008-recomendacao

## R1. D-006: percentis dos cenários

- **Decisão**: quartis da perda relativa simulada.
  - conservador = percentil 75 da perda (a produtividade que só é pior em 1 de cada 4 anos);
  - central = mediana;
  - favorável = percentil 25.
- **Motivo**: os quartis são a convenção estatística mais simples para "faixa típica" e
  aparecem lado a lado com a frequência histórica de falha. Não há norma setorial que fixe os
  percentis, por isso é uma decisão de produto, declarada em toda resposta (aviso `percentis`) e
  editável (10/25/50/75/90).

## R2. Critério de ordem

Em ordem: (1) maior margem no cenário conservador; (2) menor risco histórico de falha severa;
(3) menor risco ZARC; (4) plantio mais cedo; (5) cultura e grupo.

O critério é conservador de propósito: não premia uma alternativa que só ganha no ano favorável.
Ele vai junto da resposta (`criterio_ordem`).

## R3. Exemplo (Rio Verde-GO, textura argilosa, colheita da soja em 20/01, preço do sorgo R$ 50/sc e custo da braquiária R$ 400/ha informados)

- 32 alternativas completas e 7 indisponíveis. Os decêndios 1 da janela terminam antes da
  colheita da soja.
- No topo, a braquiária: a margem conservadora é −400 (só o custo), maior que a do milho
  (−925 conservador, +224 central, +749 favorável). Isso mostra o dilema real: o milho ganha no ano
  típico, mas perde mais no ano ruim.
- Sem preço do sorgo e sem custo da braquiária, só o milho é ranqueado. Os outros aparecem em
  `indisponiveis` com o motivo (D-005).

## R4. Grupo "não sei"

Testa todos os grupos que o ZARC publica para a cultura no município (milho: I e II; sorgo: I, II
e III; milho com braquiária: I e II). Mostra `grupos_testados` e as alternativas de cada grupo, sem
juntar.
