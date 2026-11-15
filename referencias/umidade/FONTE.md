# Fontes: umidade do solo SMAP (spec 010)

Consulta feita em **2026-11-15**. Nenhum produto foi escolhido. A escolha é a decisão
**D-008** ([#70](https://github.com/Pedrojscx/TELLUS/issues/70)), que segue pendente.
`produtos.json` traz a ficha dos três candidatos para a decisão e para o código.

## Metadados das coleções (versão, DOI, resolução)

NASA CMR, sem login:

- `https://cmr.earthdata.nasa.gov/search/collections.json?short_name=SPL3SMP&provider=NSIDC_CPRD` → V009, `C2938664585-NSIDC_CPRD`
- `...short_name=SPL3SMP_E...` → V006, `C2938664763-NSIDC_CPRD`
- `...short_name=SPL4SMGP...` → V008, `C3480440870-NSIDC_CPRD`
- `https://cmr.earthdata.nasa.gov/search/collections.umm_json?concept_id=<id>` → DOI, `GriddedResolutions` (36 km / 9 km / 9 km) e links dos guias

## Nomes das variáveis, unidades e fill values

Consultei as variáveis UMM-Var associadas a cada coleção pelo CMR
(`variables.umm_json?concept_id[]=...`). Filtrei a saída e a salvei em
`cmr_variaveis_2026-11-15.txt`. Pontos principais:

- L3 (SPL3SMP e SPL3SMP_E): `Soil_Moisture_Retrieval_Data_AM/soil_moisture` e `..._PM/soil_moisture_pm`, em `cm**3/cm**3`, com fill -9999.0. O `retrieval_qual_flag` tem fill 65534. `EASE_row_index` e `EASE_column_index` estão no próprio arquivo.
- L4 (SPL4SMGP): `Geophysical_Data/sm_surface` (0–5 cm) e `sm_rootzone` (0–100 cm), em `m3 m-3`, com fill -9999.0.

## Guias do usuário (NSIDC)

- SPL3SMP_E V006: <https://nsidc.org/sites/default/files/documents/user-guide/spl3smp_e-v006-userguide.pdf>
  (sha256 do PDF baixado: `637af534…a5ffd`)
  - §1.1: a umidade superficial representa "aproximadamente os 5 cm do topo" do solo.
  - Grade de 9 km: resolução nativa do radiômetro ≈ 36 km, interpolação Backus-Gilbert com domínio ≈ 33 km.
  - Passagem AM descendente às 6h e PM ascendente às 18h, em hora solar local no equador. As duas ficam separadas no mesmo arquivo diário.
  - Tabela 5, grade global de 9 km: 1624 linhas × 3856 colunas, `ulxmap` -17367530,45 e `ulymap` 7314540,83, EPSG:6933.
  - §2.5.3, Tabela 6, `retrieval_qual_flag` bit 0: 0 = "qualidade recomendada" e 1 = "sem qualidade recomendada". Bit 1 indica tentativa, bit 2 indica sucesso.
- SPL3SMP V009: <https://nsidc.org/sites/default/files/documents/user-guide/spl3smp-v009-userguide.pdf>
  (sha256 `2ca30191…77e3d`). Grade de 36 km com 406 × 964 células de 36.032,22 m. Usa o mesmo bit 0 de qualidade.
- SPL4SMGP V008: <https://nsidc.org/sites/default/files/documents/user-guide/multi_spl4smau-v008-userguide.pdf>
  (não baixei; a natureza "modelo com assimilação" vem do nível L4 e do título da coleção).

## Grade EASE-Grid 2.0

Projeção cilíndrica de área igual EPSG:6933 (`+proj=cea +lat_ts=30 +lon_0=0 +datum=WGS84`).
Em 2026-11-15, conferi a fórmula de `regras.ease2_xy` contra o `pyproj` 3.x (EPSG:6933) em quatro
pontos. Ela coincide até 1e-8 m. O tamanho da célula sai da extensão: 2 × 17367530,44516 m
dividido pelas colunas, o que dá 36.032,22 m (M36) e 9.008,06 m (M09). O guia V006 imprime
"9,024.31 m" na Tabela 5. Esse valor não fecha com 3856 colunas: 3856 × 9024,31 ≠ 2 × 17367530,45.
Por isso o cliente confere linha e coluna com os `EASE_row_index`/`EASE_column_index` do arquivo
baixado.

## O que não está aqui

- Nenhum dado real de umidade foi baixado. O ambiente do agente não tinha `EARTHDATA_TOKEN`.
  Os testes usam fixtures **sintéticas**, marcadas `sintetico: true`.
- A escolha do produto, da passagem (AM/PM), da camada (L4) e da regra de período fica com a D-008.
