# Data Model: 001-localizacao

Unidades: graus decimais (WGS84/SIRGAS 2000), distâncias em km arredondadas a 0,01, datas
ISO 8601.

## Procedencia

Vai junto de toda referência (Princípio I).

| Campo | Tipo | Regra |
|---|---|---|
| fonte | string | nome da fonte, ex.: "IBGE — API de malhas v3, qualidade mínima" |
| url | string | endereço consultado |
| obtido_em | date | data em que o script de preparação baixou |
| status | `fonte` \| `hipotese` | `hipotese` só para valores sem fonte (ex.: limite de 50 km) |

## Municipio

| Campo | Tipo | Regra |
|---|---|---|
| codigo_ibge | string(7) | exatamente 7 dígitos |
| nome | string | grafia oficial do IBGE |
| uf | string(2) | sigla |
| centroide | {lat, lon} | calculado do polígono; conferido com o IBGE numa amostra |
| bbox | [minLon, minLat, maxLon, maxLat] | filtro rápido antes do ponto-em-polígono |
| nome_normalizado | string | minúsculas, sem acento, para a busca (FR-005) |

## LocalEscolhido

| Campo | Tipo | Regra |
|---|---|---|
| lat | float | -90 a 90 e dentro do contorno do Brasil |
| lon | float | -180 a 180 |
| meio | `busca` \| `coordenadas` \| `mapa` \| `padrao` | como foi escolhido |
| municipio | Municipio | contém o ponto; na busca, o ponto é o centroide |
| municipio_alternativo | Municipio \| null | preenchido quando outro polígono fica a menos de 2 km (divisa) |

## Referencia

Uma por tipo, numa lista.

| Campo | Tipo | Regra |
|---|---|---|
| tipo | `celula_power` \| `celula_imerg` \| `estacao_inmet` \| `praca_conab` \| `municipio_zarc` | |
| identificador | string | ex.: "A025", "5218805", "POWER -18.000,-51.250" |
| nome | string \| null | nome da estação, praça ou município |
| lat, lon | float | centro da célula, posição da estação, centroide da praça ou do município |
| distancia_km | float | do ponto escolhido até lat/lon |
| detalhes | objeto | por tipo, veja abaixo |
| procedencia | Procedencia | obrigatório |
| avisos | Aviso[] | pode ser vazia |

Os `detalhes` dependem do tipo:
- `celula_power`: `{passo_lat: 0.5, passo_lon: 0.625}`
- `celula_imerg`: `{passo: 0.1}`
- `estacao_inmet`: `{altitude_m, situacao, inicio_operacao, uf}`
- `praca_conab`: `{uf, codigo_ibge, culturas: {soja: [2025, 2026], milho_2a_safra: [...], sorgo: [...]}, mais_proxima_por_cultura: {cultura: {nome, distancia_km}}}`
- `municipio_zarc`: `{codigo_ibge, uf}` (a disponibilidade por cultura é da spec 003)

## Aviso

| Campo | Tipo | Regra |
|---|---|---|
| codigo | string | ex.: `estacao_distante`, `praca_outro_municipio`, `divisa_ambigua`, `referencia_inexistente`, `estacao_em_pane_ignorada`, `ilha_oceanica` |
| mensagem | string | texto em português, pronto para a tela |
| referencia | string \| null | tipo da referência afetada |

## ResultadoLocalizacao

É a saída da spec e a entrada das specs 002, 003 e 006 (FR-012).

| Campo | Tipo |
|---|---|
| local | LocalEscolhido |
| referencias | Referencia[] (os 5 tipos, sempre presentes; se faltar algum, entra com aviso `referencia_inexistente`) |
| avisos | Aviso[] (a união dos avisos das referências) |
| versao_referencias | string (data do conjunto de referências usado; garante o FR-013) |
| eh_demo | bool (true para Rio Verde-GO padrão) |

## Erros

`{erro: {codigo, mensagem, campo?}}` com estes códigos:
- `coordenada_invalida`: fora da faixa ou não numérica (HTTP 422);
- `fora_do_brasil`: fora do contorno (HTTP 422);
- `fora_de_municipio`: dentro da faixa costeira, mas fora de qualquer município (HTTP 422);
- `municipio_nao_encontrado`: código IBGE inexistente (HTTP 404).

## Transições de estado

Não há estado persistente no servidor. O frontend guarda o último `LocalEscolhido` aceito e só o
troca quando chega uma resposta sem erro (US3: mantém o local anterior).
