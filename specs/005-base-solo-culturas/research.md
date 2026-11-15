# Research: 005-base-solo-culturas

Documentos lidos em 2026-11-15, entre 00h40 e 01h10 BRT (PDFs oficiais do MAPA).

## R1. Classes AD e equação oficial (D-003)

IN SPA/MAPA nº 1, de 21/06/2022, com redação da IN nº 2, de 05/08/2022.

- **Art. 2º, classes em mm/cm**: AD1 de 0,34 a menos de 0,46; AD2 de 0,46 a menos de 0,61; AD3 de
  0,61 a menos de 0,80; AD4 de 0,80 a menos de 1,06; AD5 de 1,06 a menos de 1,40; AD6 a partir de
  1,40.
- **Art. 3º, equação**, com AT, SIL e ARG em % na camada de 0 a 40 cm:
  `AD = {[1 + 0,3591·(−0,02128887·AT − 0,01005814·SIL − 0,01901894·ARG + 0,0001171219·AT·SIL + 0,0002073924·AT·ARG + 0,00006118707·SIL·ARG − 0,000006373789·AT·SIL·ARG)]^2,78474}·10`
- A equação não é monotônica na argila. Ex.: 60/15/25 dá 0,909 (AD4), 30/15/55 dá 1,043 (AD4) e
  15/15/70 dá 0,940. Por isso a textura sozinha não define a classe.

## R2. Parâmetros por cultura (portarias ZARC de GO, safra 2026/2027)

| Parâmetro | Milho 2ª safra (Port. 322) | Sorgo granífero (Port. 273) |
|---|---|---|
| Ze (raiz efetiva) | 60 cm (item 1.13) | 50 cm (item 1.8.3) |
| CAD | AD1 a AD6: 24 / 31,8 / 41,4 / 54,6 / 72,6 / 95,4 mm | tipo 1/2/3 (arenosa/média/argilosa): 35 / 55 / 75 mm |
| Grupos e fases | G I 20/30/30/20; G II 20/40/40/20; G III 20/50/50/20 dias (item 1.12) | G I ≤ 110; G II de 111 a 130; G III > 130 dias (sem fases publicadas) |
| ISNA (deficiência severa) | ≤ 0,70 na fase I; ≤ 0,55 na fase III (item 1.14) | 0,6 na fase I; 0,45 na fase III (item 1.8.4) |

Conferência: as classes AD × 60 cm do milho reproduzem as CAD da portaria (24/60 = 0,40 em AD1,
… 95,4/60 = 1,59 em AD6).

## R3. O que fica como hipótese, e por quê

| Parâmetro | Valor inicial | Motivo |
|---|---|---|
| Kc do milho | 0,30 / 1,20 / 0,60 | FAO-56, Tab. 12 (método); sem validação local |
| Kc do sorgo | 0,30 / 1,05 / 0,55 | FAO-56, Tab. 12 (método) |
| Ky do milho | total 1,25; fases 0,4 / 0,4 / 1,5 / 0,2 | FAO-33, Tab. 24 (método). A fase III do ZARC junta floração e enchimento; usa o valor da floração |
| Ky do sorgo | total 0,90; fases 0,2 / 0,2 / 0,55 / 0,2 | FAO-33, Tab. 24 (método) |
| Fases do sorgo | G I 16/28/32/24; G II 19/34/38/29; G III 22/39/45/34 | ciclos de 100, 120 e 140 dias nas proporções da FAO-56, Tab. 11 (20/35/40/30) |
| Braquiária (todos) | Ze 60, CAD do milho, fases 20/30/40/30, Kc 0,40/0,95/0,85 | não há ZARC para cobertura solteira |
| Textura → granulometria nas culturas AD | arenosa 85/5/10; média 60/15/25; argilosa 30/15/55 | ponto típico dentro da classe textural; não é medição |

## R4. Validade regional

As portarias lidas são de GO. Para outra UF, os parâmetros "fonte" passam a `hipotese` com o
motivo "aplicada fora da validade regional", até que a portaria da UF seja lida. A IN 1/2022 é
nacional (`uf: ["*"]`).
