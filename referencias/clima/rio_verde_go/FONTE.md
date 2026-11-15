# Série de clima de Rio Verde-GO (referência versionada)

Gerada por `scripts/exportar_clima_rio_verde.py` a partir do cache de `scripts/baixar_imerg.py` e
`scripts/baixar_power.py`. Metadados completos (células, versões, datas e sha256) em `meta.json`.

- Chuva: NASA GPM IMERG Final V07B, célula -17.75_-50.95 (0,1°), via OPeNDAP DAP4 (https://opendap.earthdata.nasa.gov/collections/C2723754864-GES_DISC/granules/).
- Tmax, Tmin, radiação, umidade, vento: NASA POWER diário, community AG, célula -18.000_-51.250 (https://power.larc.nasa.gov/api/temporal/daily/point).
- `power_chuva_mm` existe só para a comparação de fontes; não entra no cálculo (constituição 1.1.0).
- `imerg_situacao`: ok, sem_dado, nao_publicado (granule inexistente, D-002) ou fora_do_cache.
