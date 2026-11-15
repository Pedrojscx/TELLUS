# Research: 001-pesquisa-car-wfs

Testes feitos em 2026-11-15, por volta de 00h BRT.

## R1. Serviço WFS do SICAR (D-001)

- **Decision**: `https://geoserver.car.gov.br/geoserver/sicar/wfs`, WFS 2.0.0, sem login.
- **Camadas**: `sicar:sicar_imoveis_<uf>`, uma por UF (27). Todas aparecem no GetCapabilities
  (HTTP 200, 105 KB).
- **Campos** (DescribeFeatureType): `cod_imovel`, `status_imovel`, `dat_criacao`,
  `data_atualizacao`, `area` (ha), `condicao`, `uf`, `municipio`, `cod_municipio_ibge`,
  `m_fiscal`, `tipo_imovel` e `geo_area_imovel` (MultiPolygon). Não há nome nem CPF do
  proprietário.
- **Consulta por código**:
  `request=GetFeature&typeNames=sicar:sicar_imoveis_go&outputFormat=application/json&cql_filter=cod_imovel='GO-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33'`
  devolve 1 feição em 0,35 s, `condicao` "Aguardando análise" e `data_atualizacao` 2021-04-16.
- **Código inexistente**: `numberMatched: 0` (HTTP 200).
- **Consulta por área**: `bbox=lonmin,latmin,lonmax,latmax,EPSG:4326` (ordem lon,lat) achou 27
  imóveis em 0,05° × 0,05° perto de Rio Verde. Na ordem lat,lon, nada volta.
- **Rejected**: `consultapublica.car.gov.br` (página web com redirecionamento, sem API) e
  scraping de `car.gov.br` (SPA).

## R2. Formato do código

O código é `UF-IBGE7-HASH32`: sigla da UF, código IBGE do município (7 dígitos) e 32 caracteres
hexadecimais em maiúsculas, separados por hífen. A normalização tira espaços e pontos e passa
para maiúsculas. Um código fora desse formato dá `codigo_invalido` sem consultar a rede. A UF do
prefixo escolhe a camada.

## R3. Estados auditáveis (FR-002)

| Estado | Quando | Geometria |
|---|---|---|
| `encontrado` | 1 feição com geometria válida | candidato `aguardando_confirmacao` |
| `geometria_invalida` | feição com polígono que não passa na validação | nenhuma (oferece upload) |
| `sem_geometria` | feição sem `geo_area_imovel` | nenhuma (oferece upload) |
| `inexistente` | `numberMatched = 0` | nenhuma (oferece upload) |
| `codigo_invalido` | formato inválido, sem rede | nenhuma |
| `fonte_indisponivel` | erro de rede, 5xx ou XML de exceção, e sem cache | nenhuma (oferece upload) |

Com cache e fonte fora do ar, o estado continua o do cache, mais o aviso `cache_usado` com a data.

## R4. Validação de polígono sem GDAL

Regras em Python puro:
- anel fechado e com pelo menos 4 posições;
- coordenadas finitas e dentro do Brasil (o contorno vem de `referencias/localizacao`);
- sem autointerseção, testando segmento contra segmento em cada anel;
- área maior que 0.

Para MultiPolygon, vale para cada parte. O custo é O(n²) por anel. Com o limite de 5 mil
vértices por anel, roda em menos de 1 s; acima disso, `geometria_complexa` (D-009 ainda aberta).

## R5. Área em hectares

Projeção equivalente de Lambert azimutal, centrada no centroide, sobre a esfera de raio
6.371.008,8 m, e depois a fórmula do polígono. Para imóveis rurais, o erro contra o elipsoide fica
bem abaixo de 1%. O valor `area` do próprio CAR aparece ao lado, para conferência.

## R6. Upload do shapefile SICAR

O "demonstrativo/arquivo do imóvel" do SICAR vem num .zip com .shp, .shx, .dbf e .prj. A leitura
usa pyshp (Python puro). O `.prj` precisa ser geográfico (GEOGCS, SIRGAS 2000 ou WGS84). Se for
projetado (UTM), o erro diz "projeção não suportada; exporte em coordenadas geográficas". Quando
há várias feições, vale a união (MultiPolygon) com o aviso.

## R7. Municípios atingidos

Amostragem do polígono em grade (a mesma técnica da spec 003, com passo de 0,005°), mais os
vértices, testados contra a malha municipal do IBGE da entrega 1 da 002. A resposta lista
todos os municípios com a fração da área.
