# Quickstart: 003-dados-clima

Detalhes de campos em [data-model.md](data-model.md) e
[contracts/clima.openapi.yaml](contracts/clima.openapi.yaml).

## 1. (Opcional) Baixar os dados de um local

Precisa de `EARTHDATA_TOKEN` no `.env`, com a aplicação GES DISC autorizada.

```bash
uv run --project backend python scripts/baixar_power.py               # A025, rápido
uv run --project backend python scripts/baixar_imerg.py               # A025, ~20 min na 1ª vez
uv run --project backend python scripts/baixar_imerg.py -16.69 -49.26 # outro local
uv run --project backend python scripts/exportar_clima_rio_verde.py   # atualiza a referência versionada
```

Esperado: o IMERG imprime as situações (`ok` até 2025-09-30, `nao_publicado` depois).

## 2. Testes

```bash
cd backend && uv run pytest tests/clima -q
```

Esperado:
- caso à mão da média ponderada;
- métricas;
- rastreabilidade (10 campos);
- reprodutibilidade;
- `sem_cache`;
- segredo;
- Rio Verde: IMERG com viés -1,03% e MAE 4,13 mm/dia em 1.218 dias.

## 3. API

```bash
cd backend && uv run uvicorn tellus.api.app:app --port 8000
curl "localhost:8000/api/clima/resumo?lat=-17.785&lon=-50.965"
curl "localhost:8000/api/clima/serie?lat=-17.785&lon=-50.965&inicio=2025-01-01&fim=2025-12-31"
curl "localhost:8000/api/clima/validacao?lat=-17.785&lon=-50.965"
curl "localhost:8000/api/clima/resumo?lat=-3.1&lon=-60.0"
```

Esperado:
- a série de 2025 termina em 2025-09-30 com o aviso `lacuna_imerg`;
- a validação mostra IMERG com -1,03% e POWER com -26,96%;
- Manaus, sem cache, dá 404 `sem_cache`, com a origem citando IMERG ou POWER.
