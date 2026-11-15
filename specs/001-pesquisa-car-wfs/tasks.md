# Tasks: Pesquisa CAR WFS

**Input**: plan.md, research.md, data-model.md

**Tests**: incluídos (caso à mão de área e validação; estados distintos; portões da constituição).

Issues relacionadas: #1 a #18 (US-001, T-001 a T-006).

## Phase 1: Setup

- [X] T001 Acrescentar `pyshp` ao `backend/pyproject.toml` (versão conferida no PyPI) e criar `backend/src/tellus/car/__init__.py`
- [X] T002 [P] Criar `referencias/car/limites.json` com `max_vertices_anel: 5000` (hipótese, D-009) e `casas_decimais_id: 6`

## Phase 2: Foundational (regras puras)

- [X] T003 Implementar `backend/src/tellus/car/regras.py`:
  - `normalizar_codigo`, que valida `^[A-Z]{2}-\d{7}-[0-9A-F]{32}$` depois de tirar espaços e pontos e passar para maiúsculas;
  - `validar_poligono`, que devolve a lista de motivos: anel aberto, menos de 4 posições, coordenada não finita, autointerseção, área zero, vértices demais;
  - `area_ha` por Lambert azimutal equivalente;
  - `id_geometria` (sha256 do GeoJSON com 6 casas);
  - `municipios_atingidos(geom, malha)`, por amostragem de 0,005° mais os vértices, com frações que somam 1.
- [X] T004 [P] Testes de regras em `backend/tests/car/test_regras.py`:
  - quadrado de 0,01° × 0,01° no equador ≈ 123,6 ha (conta à mão: 1.111,95 m × 1.111,95 m);
  - laço em "8" dá `autointersecao`;
  - anel aberto;
  - código com minúsculas e pontos é normalizado;
  - código curto é inválido.

## Phase 3: US1 - Verificar um CAR (#1, #2, #3, #4, #7)

- [X] T005 [US1] Implementar `backend/src/tellus/car/wfs.py`: consulta por `cql_filter=cod_imovel='...'` na camada da UF, com timeout de 20 s. Guarda a resposta em `data/raw/car/<codigo>.json` mais o `.meta.json` (url, data, sha256). Lê o cache quando a fonte falha
- [X] T006 [US1] Implementar `backend/src/tellus/car/servico.py` `consultar(codigo)`, que devolve a `ConsultaCar` com os 6 estados do research R3, a proveniência, a qualidade, o candidato (área, municípios, `id_geometria`) e a alternativa de upload
- [X] T007 [US1] Rota `GET /api/car/{codigo}` em `backend/src/tellus/api/car.py`, registrada no `app.py`
- [X] T008 [P] [US1] Testes `backend/tests/car/test_servico.py` com respostas WFS gravadas em `backend/tests/car/fixtures/` (encontrado, vazio, sem geometria, geometria inválida) e falha de rede simulada: cada caso dá um estado distinto, nenhum inventa geometria e o cache é usado com aviso

## Phase 4: Upload SICAR e confirmação (#11, #13)

- [X] T009 [US1] Implementar `backend/src/tellus/car/shapefile.py`: ler o zip com pyshp, exigir .shp, .shx e .dbf, exigir `.prj` geográfico (quando presente) e unir as feições
- [X] T010 [US1] `servico.upload_sicar(bytes)` e `servico.confirmar(geometria, id_geometria)`, que valida de novo, confere o id e devolve a `Lavoura` com a localização da 002 no centroide
- [X] T011 [US1] Rotas `POST /api/car/upload` (multipart) e `POST /api/lavoura/confirmar`
- [X] T012 [P] [US1] Testes `backend/tests/car/test_upload.py`: shapefile gerado no teste com pyshp; zip sem .dbf; `.prj` UTM recusado; confirmação com id divergente recusada

## Phase 5: Tela e validação (#16)

- [X] T013 [US1] `frontend/src/components/ConsultaCar.astro`:
  - campo "Número do CAR", com o estado em linguagem simples;
  - polígono no mapa, área, municípios, condição no CAR e fonte;
  - botão "Confirmar esta área" e, quando não há geometria, o upload do shapefile SICAR.
- [X] T014 (feito como conferência manual em 15/11 00h, não como teste automático) Teste de integração com o WFS real: o código de exemplo de Rio Verde volta `encontrado`
- [X] T015 Registrar no `REGISTRO.md` e no `MAPA_FEATURES.md`; comentar e fechar as issues #1 a #18 (feito em 15/11, autorizado pelo Pedro)
