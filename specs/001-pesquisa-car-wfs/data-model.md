# Data Model: 001-pesquisa-car-wfs

## ConsultaCar

| Campo | Tipo | Regra |
|---|---|---|
| codigo_informado | string | como o produtor digitou |
| codigo | string \| null | normalizado, no formato `^[A-Z]{2}-\d{7}-[0-9A-F]{32}$` |
| estado | enum | `encontrado`, `geometria_invalida`, `sem_geometria`, `inexistente`, `codigo_invalido`, `fonte_indisponivel` |
| consultado_em | date | data da resposta usada (do cache, se veio dele) |
| proveniencia | {fonte, versao, url, camada, obtido_em} | versão = "SICAR WFS 2.0.0" |
| qualidade | {condicao, status_imovel, data_atualizacao, tipo_imovel, area_declarada_ha} \| null | campos do CAR |
| candidato | CandidatoLavoura \| null | só quando `encontrado` |
| alternativa | {upload_sicar: true, mensagem} \| null | quando não há geometria utilizável |
| avisos | Aviso[] | `cache_usado`, `limite_declarado` |
| erros_geometria | string[] | quando `geometria_invalida` |

## CandidatoLavoura

É a mesma estrutura usada pela spec 002 para desenho e upload.

| Campo | Tipo | Regra |
|---|---|---|
| id_geometria | string | sha256 do GeoJSON canônico (coordenadas com 6 casas) |
| geometria | GeoJSON Polygon \| MultiPolygon | WGS84/SIRGAS 2000 |
| origem | `car` \| `upload_sicar` \| `desenho` \| `arquivo` | |
| area_ha | float | calculada (R5), com 2 casas |
| municipios | [{codigo_ibge, nome, uf, fracao}] | soma 1 (R7) |
| centroide | {lat, lon} | |
| estado | `aguardando_confirmacao` | |
| proveniencia | {fonte, obtido_em, codigo_car?} | |

## Lavoura (confirmada)

É o `CandidatoLavoura` com `estado: "confirmada"`, mais `confirmada_em` e a
`localizacao` (ResultadoLocalizacao da 002, resolvido no centroide). Para confirmar, é preciso
reenviar a geometria. O servidor valida de novo e confere o `id_geometria` (FR-004: sem
confirmação, nada segue).

## Erros de upload

`{erro: {codigo, mensagem, campo}}`, com estes códigos:
- `arquivo_invalido` (não é zip, ou faltam .shp/.dbf/.shx);
- `sem_geometria`;
- `projecao_nao_suportada`;
- `geometria_invalida` (com a lista de motivos);
- `geometria_complexa`.
