# Entrega 2 da 002: área por desenho e por arquivo (#20, #21, #22, #24, #30, #31, #32)

## Os seis modos de entrada

| Modo | Rota | Como entra | Confirmação |
|---|---|---|---|
| Marcação (ponto) | `/api/localizacao*` | entrega 1 (busca, coordenadas, clique) | o pedido de cálculo do contrato (011) só aceita `area.confirmada = true` |
| Desenho | `POST /api/lavoura/desenho` `{geometria}` | Leaflet puro (clique marca vértice; desfazer, fechar e conferir, limpar), sem plugin | `POST /api/lavoura/confirmar` (a mesma do CAR) |
| KML | `POST /api/lavoura/arquivo` | `xml.etree`; um Placemark (Polygon ou MultiGeometry); DOCTYPE/ENTITY recusados | idem |
| KMZ | idem | `zipfile` + o KML interno (`doc.kml` ou o primeiro `.kml`); tamanho descompactado limitado | idem |
| GeoJSON | idem | `json`; FeatureCollection, Feature ou Geometry; `crs` não geográfico recusado | idem |
| Shapefile .zip | idem (e `/api/car/upload`, inalterado) | `tellus.car.shapefile` (pyshp, já existente) | idem |

Todos os modos de área passam pela mesma validação (`car.regras.validar_poligono`, limite técnico por anel), pelos limites
da D-009 (`contrato.regras.limites_excedidos`) e pelo mesmo resumo territorial (`car.servico.candidato`: área em ha,
todos os municípios atingidos e `id_geometria`, que é igual entre formatos para a mesma geometria). A confirmação de
`desenho` e `arquivo` checa os limites de novo. CAR e SICAR seguem como antes.

## Erros nomeados (#24, SC-002)

- `formato_nao_aceito`: extensão fora de KML, KMZ, GeoJSON (.geojson/.json) e .zip.
- `arquivo_invalido`: XML/JSON/zip corrompido, KMZ sem .kml, coordenada malformada, DOCTYPE ou ENTITY.
- `projecao_nao_suportada`: .prj projetado ou `crs` não geográfico.
- `sem_geometria`: nenhum Polygon/MultiPolygon.
- `varias_lavouras`: mais de um polígono separado no arquivo (uma lavoura por envio; MultiPolygon = uma lavoura em partes).
- `geometria_invalida`: anel aberto, menos de 4 posições, autointerseção, fora da faixa geográfica, área nula ou mais de 5.000 vértices num anel.
- `vertices_excedidos`: acima de 10.000 vértices no total. A mensagem pede para simplificar ou dividir.
- `area_excedida`: acima de 100.000 ha. A mensagem pede para dividir.
- `arquivo_grande`: HTTP 413, acima de 20 MB (ou o conteúdo descompactado do KMZ/.zip acima disso).

Os limites são lidos de `backend/src/tellus/contrato/limites.json` (D-009, hipótese).

## Testar o desenho na tela

1. `cd backend && uv run uvicorn tellus.api.app:app --port 8000`
2. Em outro terminal: `cd frontend && npm run dev` e abrir `http://localhost:4321`.
3. Aproximar o mapa de Rio Verde-GO, clicar em **Desenhar área** e clicar no mapa nos cantos da lavoura (mínimo 3).
   Use **Desfazer ponto** se errar.
4. **Fechar e conferir**: aparece o resumo (área em ha, municípios, fonte). Depois, **Confirmar esta área**.
5. Para ver os erros: desenhe um "8" (os lados se cruzando) → `geometria_invalida`. Ou envie um arquivo .pdf → `formato_nao_aceito`.
