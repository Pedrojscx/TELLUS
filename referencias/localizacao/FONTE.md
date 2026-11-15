# Fontes das referências de localização

Gerado por `scripts/preparar_localizacao.py`. Os arquivos brutos ficam em
`data/raw/localizacao/` (fora do Git), cada um com `.meta.json` (url, data, sha256).

| Arquivo bruto | Fonte | URL | Obtido em |
|---|---|---|---|
| municipios.json | IBGE — API de localidades v1 (municípios) | https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado | 2026-11-14 |
| malha_municipios.geojson | IBGE — API de malhas v3, municípios, qualidade mínima | https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=municipio | 2026-11-14 |
| brasil.geojson | IBGE — API de malhas v3, contorno do país, qualidade mínima | https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&qualidade=minima | 2026-11-14 |
| estacoes_inmet.json | INMET — catálogo de estações automáticas | https://apitempo.inmet.gov.br/estacoes/T | 2026-11-14 |
| conab_soja.xls | Conab — série histórica de custos de produção, soja | https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/arquivos-custo-de-producao/agricolas/serie-historica-custos-soja-1997-a-2026.xls | 2026-11-14 |
| conab_milho_2a_safra.xls | Conab — série histórica de custos de produção, milho 2ª safra | https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/arquivos-custo-de-producao/agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls | 2026-11-14 |
| conab_sorgo.xls | Conab — série histórica de custos de produção, sorgo | https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/arquivos-custo-de-producao/agricolas/seriehistoricacustossorgo2013a2026.xls | 2026-11-14 |

Derivados neste diretório:
- `municipios.json`: lista IBGE + centroide e bbox calculados do polígono da malha.
  Municípios sem polígono na malha mínima ficam com `centroide: null` e não são resolvidos.
- `malha_municipios.geojson`, `brasil.geojson`: cópia da malha IBGE (qualidade mínima).
- `estacoes_inmet.json`: estações automáticas, com situação (Operante/Pane).
- `pracas_conab.json`: praças com planilha de custo de 2025 ou 2026 (soja, milho 2ª safra,
  sorgo), ligadas ao código IBGE; coordenada = centroide do município.
- `limites.json`: limites de aviso, marcados como hipótese.

versao_referencias: 2026-11-14
