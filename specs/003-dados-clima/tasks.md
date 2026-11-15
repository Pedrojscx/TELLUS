# Tasks: Dados de clima

**Input**: plan.md, spec.md, research.md, data-model.md, contracts/clima.openapi.yaml

**Tests**: incluídos (portões da constituição: rastreabilidade, reprodutibilidade, caso à mão,
queda de fonte e segredos).

## Phase 1: Setup

- [ ] T001 Acrescentar `h5py` ao `backend/pyproject.toml` (versão conferida no PyPI) e criar `backend/src/tellus/clima/__init__.py`
- [ ] T002 [P] Criar `referencias/clima/limites.json` com `contagem_minima_imerg: 1` (status `fonte`: precipitation_cnt > 0 indica amostras válidas, documentação IMERG) e `passo_amostragem_graus: 0.005` (status `hipotese`)

## Phase 2: Foundational

- [ ] T003 Implementar `backend/src/tellus/clima/imerg.py`:
  - `CelulaImerg.do_ponto` com índices floor((lat+90)/0,1) e floor((lon+180)/0,1);
  - restrição DAP4 da célula e leitura `.dap.nc4` com h5py;
  - 404 gravado como `nao_publicado`, valor inválido como `sem_dado`, rede como `falha_rede` (refeito na próxima rodada);
  - CSV por célula em `data/raw/clima/imerg/` com `data,chuva_mm,contagem,situacao,obtido_em`;
  - token só de `EARTHDATA_TOKEN`.
- [ ] T004 [P] Implementar `backend/src/tellus/clima/power.py`: um pedido diário do POWER para o período (`T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,RH2M,WS2M,PRECTOTCORR`, `community=AG`, `time-standard=UTC`), guardado em `data/raw/clima/power/<lat>_<lon>.json` com `.meta.json` (url, data, sha256), mais a leitura com -999 virando `None`
- [ ] T005 [P] Implementar `backend/src/tellus/clima/regras.py`, puro:
  - `pesos_celulas(geometria)`: ponto dá peso 1; polígono usa amostragem de 0,005° e devolve pesos que somam 1;
  - `chuva_ponderada(valores_por_celula, pesos)`, que dá `None` se alguma célula com peso > 0 estiver sem valor;
  - `metricas(referencia, fonte)` com total, viés %, MAE, RMSE e fração ≥ 1 mm.
- [ ] T006 [P] Testes de regras em `backend/tests/clima/test_regras.py`: caso à mão de 2 células com pesos 0,25 e 0,75 em 3 dias (dia 3 com uma célula ausente dá `None`); métricas num conjunto de 4 dias calculado à mão; polígono inteiro dentro de uma célula dá peso 1
- [ ] T007 Scripts `scripts/baixar_imerg.py` e `scripts/baixar_power.py` (ponto padrão = A025). O token vai do `.env` para o ambiente sem ser exibido

## Phase 3: US1 - Conferir a chuva usada (P1) 🎯 MVP

- [ ] T008 [US1] Implementar `backend/src/tellus/clima/referencias.py`: localizar o cache (`data/raw/clima`) e, sem cache, a exportação versionada `referencias/clima/rio_verde_go/serie_diaria.csv`
- [ ] T009 [US1] Implementar `backend/src/tellus/clima/servico.py`:
  - `serie(lat, lon, inicio, fim)` monta a `SerieClimatica` com a chuva IMERG ponderada e as variáveis POWER;
  - proveniência completa para chuva e para POWER, conforme o data-model;
  - `ultimo_dia_publicado_imerg` e o aviso `lacuna_imerg` quando o pedido passa dessa data;
  - erro `sem_cache` com origem quando não há dados.
- [ ] T010 [US1] Rotas `GET /api/clima/resumo` e `GET /api/clima/serie` em `backend/src/tellus/api/clima.py`, registradas no `app.py`; handler de `ErroClima` no formato `{erro: {codigo, mensagem, origem}}`
- [ ] T011 [P] [US1] Teste de rastreabilidade em `backend/tests/clima/test_rastreabilidade.py`: cada proveniência tem os 10 campos preenchidos e nenhum `DiaClima` tem chuva vinda do POWER
- [ ] T012 [P] [US1] Teste de reprodutibilidade (dois pedidos iguais dão respostas idênticas) e de queda de fonte (diretório de cache vazio dá `sem_cache` com origem) em `backend/tests/clima/test_servico.py`

## Phase 4: US2 - Validação local INMET (SC-002)

- [ ] T013 [US2] Em `servico.py`, `validacao(lat, lon, recorte)`: para a A025, parear a coluna `inmet` (com `paired=True`) de `data/processed/pesquisa_chuva/daily_all_sources.csv` com o IMERG do cache e a chuva POWER do cache. Para outras estações, devolver `disponivel: false` com o motivo
- [ ] T014 [US2] Rota `GET /api/clima/validacao`
- [ ] T015 [US2] Teste `backend/tests/clima/test_rio_verde.py` (SC-002): jan–jun, 1.218 dias, IMERG com viés -1,03% ± 0,05 e MAE 4,13 ± 0,02 mm/dia; POWER com viés -26,96% ± 0,05

## Phase 5: Polish

- [ ] T016 `scripts/exportar_clima_rio_verde.py` gera `referencias/clima/rio_verde_go/serie_diaria.csv` e o `FONTE.md` (fontes, versão, período, sha256 dos brutos)
- [ ] T017 [P] Teste de segredo em `backend/tests/clima/test_segredo.py`: com `EARTHDATA_TOKEN=tok-teste`, nenhum arquivo de cache, `.meta.json` ou resposta da API contém o valor
- [ ] T018 Rodar `quickstart.md`, registrar no `REGISTRO.md` e atualizar o status em `docs/sdd/MAPA_FEATURES.md`

## Dependencies

Setup → Foundational (T003 a T007) → US1 (T008 a T012) → US2 (T013 a T015) → Polish. T004, T005 e
T006 são paralelas a T003. A US2 precisa do cache completo do IMERG de Rio Verde (download de
cerca de 20 min).

## Implementation Strategy

MVP = US1 com Rio Verde vindo do cache. A US2 prova a qualidade (SC-002). O Polish garante a demo
offline em qualquer máquina.
