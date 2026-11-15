# Data Model: 006-motor-hidrico-entressafra

## Pedido (`POST /api/motor/simular` e `/api/motor/janela`)

```json
{
  "lat": -17.785,
  "lon": -50.965,
  "codigo_ibge": null,
  "cultura": "milho_2a_safra | sorgo_granifero_2a_safra | braquiaria_cobertura",
  "grupo": "GRUPO I",
  "solo": {"textura": null, "granulometria": null, "classe": null, "cad_mm": null},
  "data_colheita_soja": "AAAA-MM-DD ou MM-DD",
  "data_plantio": "opcional; padrão = colheita + 3 dias",
  "entressafra": {"manejo": "pousio | palhada", "kc": null},
  "armazenamento_inicial_frac": 1.0,
  "edicoes": {"kc.med": 1.1}
}
```

## Resposta de `/simular`

- `resultado`:
  - `risco_historico_falha_severa`: fração dos anos válidos;
  - `definicao_falha`, `anos_validos`, `anos_com_falha`, `deficit_mm_mediano`;
  - `perda_relativa_quantis`: {10, 25, 50, 75, 90}, ou null sem Ky;
  - `risco_zarc_pct`, `significado_riscos`.
- `por_ano[]`: `ano`, `plantio`, `maturacao`, `agua_no_plantio_frac`, `isna_fases[4]`,
  `deficit_mm_fases[4]`, `deficit_mm`, `etc_mm`, `eta_mm`, `chuva_mm`, `drenagem_mm`,
  `perda_relativa`, `falha_severa`, `dr_final`.
- `anos_excluidos[]`: {ano, motivo}. Dia ausente interrompe o ano.
- `entradas`: clima, solo, cultura, estado_inicial, entressafra e zarc, cada um com origem, status e
  `hash`; mais `versao_entradas`.
- `avisos[]`: `nao_e_previsao`, `escala_regional`, `hipoteses`, `anos_excluidos`, `amostra_pequena`.

## Resposta de `/janela`

`{cultura, grupo, codigo_ibge, solo, data_colheita_soja, portaria, decendios: [{decendio, data_plantio, risco_zarc_pct, situacao, risco_historico_falha_severa, anos_validos, deficit_mm_mediano, perda_relativa_quantis}], avisos}`

O campo `situacao` vale `simulado` ou `antes_da_colheita`.

## Erros

`{erro: {codigo, mensagem, campo}}`, com estes códigos:
- `fora_da_janela_zarc` (422);
- `zarc_indisponivel` (409);
- `solo_sem_classe_zarc`, `solo_indisponivel`, `grupo_invalido`, `data_invalida`, `fora_do_dominio`, `manejo_invalido`;
- os erros das specs 002, 003 e 005.
