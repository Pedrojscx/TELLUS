# Data Model: 008-recomendacao

## Pedido (`POST /api/recomendacao`)

`{metodologia: "cultura_escolhida" | "calculo_completo", cultura? (obrigatória na cultura escolhida), grupo? (vazio = "não sei"), lat, lon, codigo_ibge?, solo, data_colheita_soja, entressafra?, armazenamento_inicial_frac?, edicoes_cultura?: {cultura: {...}}, edicoes_economia?: {cultura: {...}}, percentis?}`

## Alternativa

| Campo | Origem |
|---|---|
| cultura, grupo, decendio, data_plantio | ZARC (004) e motor (006) |
| risco_zarc_pct, portaria_zarc | 004, risco oficial |
| risco_historico_falha_severa, anos_validos, deficit_mm_mediano, perda_relativa_quantis | 006, frequência simulada |
| margem_r_ha {conservador, central, favoravel}, cenarios | 007 |
| unidades | R$/ha, fração dos anos, %, mm |
| versoes {motor, economia} | `versao_entradas` (006) e `versao_premissas` (007) |
| hipoteses[] | avisos de hipótese do motor, percentis e premissas editadas |
| posicao | ordem no ranking |

## Resposta

`{metodologia, criterio_ordem[], grupos_testados{cultura: [grupos]}, grupo_informado, recomendada (1ª alternativa ou null), alternativas[] (ordenadas), indisponiveis[] (cultura, grupo, decendio, motivo), avisos[]}`

Os avisos são `nao_e_previsao`, `riscos_distintos`, `percentis` e, quando não há alternativa
completa, `sem_recomendacao`.
