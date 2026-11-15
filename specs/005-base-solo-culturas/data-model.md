# Data Model: 005-base-solo-culturas

## Parâmetro agronômico (resposta de `/api/culturas/{cultura}/parametros`)

| Campo | Tipo | Regra |
|---|---|---|
| id | string | `ze_cm`, `cad_mm`, `fases_dias`, `ciclo_dias`, `isna_limite`, `kc`, `ky` |
| nome, unidade | string | sempre preenchidos |
| valor_padrao | número \| objeto | valor da base, nunca sobrescrito |
| valor_usado | número \| objeto | igual ao padrão, ou o valor editado |
| editado | bool | |
| status | `fonte` \| `hipotese` | `fonte` exige `fonte` e `trecho` |
| fonte | {id, documento, url, consultado_em, validade_regional} \| null | null quando é hipótese |
| trecho | string \| null | item da portaria ou artigo da IN |
| metodo_referencia | `FAO-56` \| `FAO-33` \| null | método, nunca fonte |
| motivo | string \| null | obrigatório quando é hipótese |

## Premissas (`POST /api/culturas/premissas`)

O pedido é `{cultura, uf, edicoes: {"kc.med": 1.1, "ze_cm": 70, "fases_dias.GRUPO I": [20,30,30,20]}}`.
A resposta são os parâmetros com `valor_usado` aplicado, mais
`alteracoes: [{parametro, valor_anterior, valor_novo, unidade, origem_novo}]`.

Domínio aceito:
- ze_cm de 10 a 300;
- cad_mm de 5 a 300;
- fases_dias de 1 a 150;
- isna_limite de 0 a 1;
- kc de 0,1 a 1,6;
- ky de 0 a 2,5.

Fora disso, erro `fora_do_dominio`.

## Classificação de solo (`POST /api/solo/classificar`)

O pedido traz `{cultura, uf, textura | granulometria{areia, silte, argila} | classe | cad_mm}`. A
precedência é cad_mm, depois classe, depois granulometria, depois textura.

A resposta é `{cultura, classe, cad_mm, ad_mm_cm, origem, status, passos[], aviso}`:
- `origem` é `produtor`, `classe`, `granulometria` ou `textura`;
- `status` é `fonte`, `hipotese`, `editado` ou `indisponivel`;
- cada passo traz o próprio status e fonte, por isso a hipótese se propaga.
