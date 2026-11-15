# Research: 006-motor-hidrico-entressafra

## R1. Método

- **ETo**: FAO-56, Penman-Monteith diária (eq. 6). A umidade entra pela UR média (eq. 19), porque
  o POWER entrega RH2M diária. A altitude é a da célula POWER, devolvida pela API (731,58 m em
  Rio Verde). G = 0. Conferida contra o Exemplo 18 da FAO-56: Rn 13,28 e ETo 3,9 mm/dia.
- **Balanço**: FAO-56, cap. 8, com Kc único:
  - Ks pela eq. 84, calculado com o Dr do dia anterior;
  - Dr pela eq. 85;
  - drenagem acima da capacidade de campo;
  - chuva toda efetiva (sem escoamento superficial, premissa declarada).
- **Curva de Kc**: constante na fase I, linear na II, constante na III, linear na IV (FAO-56,
  fig. 25), com as fases do ZARC.
- **Produtividade**: FAO-33, Ya/Ym = Π(1 − Ky_i·(1 − ETa_i/ETc_i)) por fase (forma multiplicativa).
- **Falha severa**: critério do ZARC (Port. 322/273). ISNA = ETr/ETc da fase I ou da fase III
  abaixo ou igual ao limite. Por isso o risco histórico do TELLUS é comparável, em conceito, ao
  risco oficial, embora use outra série e outro período.

## R2. Conferência qualitativa em Rio Verde-GO

Colheita da soja em 01/01; plantio no 1º dia de cada decêndio; solo AD4 (milho) e tipo 3 (sorgo);
grupo I; série 2001 a 2025.

| Decêndio | Milho: ZARC / histórico | Sorgo: ZARC / histórico |
|---|---|---|
| 1 a 3 (jan) | 20% / 0% | 20% / 0% |
| 4 (01/02) | 20% / 8% | 20% / 0% |
| 5 (11/02) | 40% / 28% | 20% / 0% |
| 6 (21/02) | fora | 20% / 8% |
| 7 (01/03) | fora | 20% / 20% |
| 8 (11/03) | fora | 20% / 28% |
| 9 (21/03) | fora | 30% / 32% |

O risco sobe com o plantio tardio e o sorgo aguenta cerca de um mês a mais que o milho, como no
ZARC e no REGISTRO (14/11). Exemplo pontual: milho com plantio em 04/02 dá 25 anos válidos,
falha em 3 (12%), déficit mediano de 46 mm e perda mediana de 22%.

## R3. D-004: estado inicial e entressafra

Não há medição de umidade do solo na colheita, então ficam como hipóteses editáveis em
`referencias/motor/premissas.json`:
- estado inicial com 100% da CAD;
- Kc do pousio 0,30;
- Kc da palhada 0,15 (FAO-56, cap. 11: cerca de 5% menos evaporação a cada 10% de cobertura);
- intervalo colheita → plantio de 3 dias.

## R4. Limitações declaradas

- O balanço não modela escoamento superficial nem ascensão capilar.
- A Ze é fixa (a da portaria), sem crescimento de raiz.
- O mesmo dia do calendário vale para todos os anos.
- A braquiária não tem Ky: entra só o risco de falha de estabelecimento (hipótese) e o déficit.
