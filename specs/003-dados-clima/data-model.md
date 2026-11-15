# Data Model: 003-dados-clima

## Proveniencia (Princípio I)

| Campo | Tipo | Regra |
|---|---|---|
| fonte | string | ex.: "NASA GPM IMERG Final" |
| versao | string | ex.: "GPM_3IMERGDF V07B" ou "POWER daily (MERRA2, SYN1DEG)" |
| periodo | {inicio, fim} | datas ISO dos dias entregues |
| unidade | string | por variável: mm/dia, °C, MJ/m²/dia, %, m/s |
| localizacao | objeto | IMERG: `celulas[{centro_lat, centro_lon, peso}]`; POWER: `{lat, lon, altitude_m}` |
| qualidade | objeto | `dias_validos`, `dias_ausentes`, `dias_nao_publicados`, `contagem_media` (IMERG) |
| resolucao | string | "0,1° × 0,1°, diária" ou "0,5° × 0,625°, diária" |
| aviso_escala | string | texto fixo do Princípio IV |
| obtido_em | date | data do download mais recente usado |
| url | string | endereço da fonte |

## DiaClima

| Campo | Tipo | Regra |
|---|---|---|
| data | date | dia UTC |
| chuva_mm | float \| null | IMERG ponderado; null se qualquer célula com peso > 0 estiver sem dado |
| tmax_c, tmin_c | float \| null | POWER; -999 vira null |
| radiacao_mj_m2 | float \| null | POWER ALLSKY_SFC_SW_DWN |
| umidade_pct | float \| null | POWER RH2M |
| vento_m_s | float \| null | POWER WS2M (2 m) |

A chuva do POWER **não** aparece em `DiaClima`.

## SerieClimatica

`{local: {lat, lon}, dias: DiaClima[], proveniencia: {chuva: Proveniencia, power: Proveniencia}, ultimo_dia_publicado_imerg: date, avisos: Aviso[], origem_dados: "cache" | "referencia_versionada", versao_cache: date}`

## ValidacaoLocal

`{estacao: {codigo, nome, distancia_km}, periodo, recorte: "jan-jun" | "todos", dias_pareados, dias_excluidos: {motivo: n}, metricas: {inmet: {total_mm, frac_dias_chuva}, imerg: {...}, power: {...}}}`

Cada métrica de fonte traz `total_mm`, `vies_pct`, `mae_mm_dia`, `rmse_mm_dia` e
`frac_dias_chuva` (≥ 1 mm). Quando a estação não tem série preparada, vem
`{disponivel: false, motivo}`.

## Avisos (códigos)

`lacuna_imerg`, `cache_desatualizado`, `celula_parcial`, `validacao_indisponivel`, `escala_regional`

## Erros

`{erro: {codigo, mensagem, origem}}`: `sem_cache` (404; a origem nomeia a fonte),
`sem_credencial` (503), `fonte_indisponivel` (503), `coordenada_invalida` (422)
