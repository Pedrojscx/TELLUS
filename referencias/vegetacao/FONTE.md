# Fontes — vegetação (spec 009)

## Arquivos

| Arquivo | Conteúdo | Natureza |
|---|---|---|
| `produtos.json` | metadados de MOD13Q1, MYD13Q1 e HLS v2.0: versão, DOI, resolução, escala, faixa válida, preenchimento, significado das camadas de QA, grade senoidal | fato documentado do produto |
| `parametros.json` | produto, índice, janela, mínimo de composições, regra de qualidade, cobertura mínima | **hipótese operacional do protótipo** (D-007, #69), status `hipotese` |
| `series/<chave_area>/MOD13Q1.csv` + `.meta.json` | série derivada (por pixel) para a demo offline | dado real, derivado do bruto em `data/raw/vegetacao/` |

## Documentos

- Didan, K.; Barreto Munoz, A. *MODIS Collection 6.1 (C61) Vegetation Index Product User Guide*
  (MOD13 Series), Version 3.10, setembro de 2019. NASA LP DAAC.
  <https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf>
  - seção 5.2 *Scientific Data Sets*, Tabela 1: NDVI/EVI int16, faixa −2000 a 10000, preenchimento −3000,
    fator 0,0001; VI Quality uint16, preenchimento 65535; pixel reliability int8, preenchimento −1.
  - seção 5.5.2 *QA Science Data Sets*, Tabela 4 (*Pixel Reliability*): −1 Fill/No Data; 0 Good Data
    "Use with confidence"; 1 Marginal data "Useful, but look at other QA information"; 2 Snow/Ice;
    3 Cloudy.
  - seção 5.5.2, Tabela 5 (*VI Quality*): bits 0–1 MODLAND QA (00 boa qualidade, 01 conferir outras
    QA, 10 provavelmente nuvem, 11 não produzido); bit 8 nuvem adjacente; bit 10 nuvens mistas;
    bit 14 possível neve/gelo; bit 15 possível sombra.
- MOD13Q1 v061 — DOI 10.5067/MODIS/MOD13Q1.061; MYD13Q1 v061 — DOI 10.5067/MODIS/MYD13Q1.061.
- Ju, J. et al. *Harmonized Landsat and Sentinel-2 (HLS) Product User Guide*, Product Version 2.0,
  última atualização abril de 2026. <https://lpdaac.usgs.gov/documents/1698/HLS_User_Guide_V2.pdf>
  - seção 6.4 *Quality Assessment Layer*, Tabela 9: bit 0 cirro (reservado, não usado na v2.0);
    1 nuvem; 2 adjacente a nuvem/sombra; 3 sombra de nuvem; 4 neve/gelo; 5 água; 6–7 aerossol.
  - HLSL30 v2.0 — DOI 10.5067/HLS/HLSL30.020; HLSS30 v2.0 — DOI 10.5067/HLS/HLSS30.020.
- EVI: Huete, A. et al. 2002. *Remote Sensing of Environment* 83:195–213.
- Grade senoidal MODIS: Wolfe, R.; Roy, D.; Vermote, E. 1998. *IEEE TGRS* 36(4):1324–1338.

## Acesso

- ORNL DAAC MODIS Web Service (`https://modis.ornl.gov/rst/api/v1/`): **sem login**. Usado por
  `scripts/preparar_vegetacao.py`. Respostas lentas (cerca de 50 s por pedido, no máximo 10 datas).
- NASA CMR (`https://cmr.earthdata.nasa.gov/search/`): catálogo de grânulos HLS, **sem login**.
- Arquivos HLS (`data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/...`): **exigem NASA Earthdata
  login** (o pedido sem credencial é redirecionado com 302 para `urs.earthdata.nasa.gov`). Credencial
  só por `EARTHDATA_TOKEN` no ambiente, nunca no Git.

## Recriar

```bash
cd backend && uv run python ../scripts/preparar_vegetacao.py --lat -17.785278 --lon -50.965 --meses 12 \
  --exportar-referencia rio_verde_go
```
