# Research: 001-localizacao

Fontes testadas em 2026-11-14, por volta de 22h50 BRT, a partir da máquina do LK.

## R1. Lista de municípios, UF e código IBGE

- **Decision**: API de localidades do IBGE,
  `https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado`.
- **Evidence**: HTTP 200, 2,4 MB, 0,4 s, sem login. Retornou 5.571 municípios com `municipio-id`
  (7 dígitos), nome, UF e regiões. Rio Verde-GO = 5218805; também existe "Rio Verde de Mato
  Grosso"-MS = 5007406, o que confirma o cenário de busca da spec.
- **Alternatives**: a planilha DTB do IBGE (mesmo conteúdo, formato menos prático); listas de
  terceiros no GitHub (não oficiais, descartadas pelo Princípio I).

## R2. Ponto → município (e "fora do Brasil")

- **Decision**: malha municipal do IBGE, em qualidade mínima, num GeoJSON único:
  `https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio`.
  O contorno do país vem da mesma API, sem `intrarregiao`. Para achar o município, primeiro filtra
  pelo retângulo envolvente e depois testa ponto-em-polígono (ray casting) em Python puro.
- **Evidence**: malha com 5.570 polígonos, 3,6 MB, 0,4 s. País: 1 MultiPolygon, 12,7 KB. A
  qualidade intermediária tem 12,3 MB.
- **Rationale**: 3,6 MB cabem no repositório como referência derivada. Python puro evita
  dependência geoespacial (shapely/GDAL não estão instalados, segundo o REGISTRO) e mantém a regra
  pura (Princípio IV).
- **Risk**: a malha mínima simplifica as divisas, então perto delas o município pode sair errado.
  Mitigação: se o ponto estiver a menos de 2 km de outro polígono, a resposta mostra o vizinho
  como alternativa (edge case da spec). A lista tem 5.571 municípios e a malha tem 5.570; o
  município faltante será identificado na tarefa de preparação e registrado.
- **Alternatives**: malha intermediária (mais precisa, 3,4× maior; fica como troca futura);
  geocodificação reversa de terceiros como Nominatim (depende de rede e não é oficial).

## R3. Centroide do município (busca por nome → ponto)

- **Decision**: centroide calculado do polígono da malha (R2). O centroide oficial do IBGE serve
  de conferência.
- **Evidence**: `api/v3/malhas/municipios/5218805/metadados` devolve o centroide (-17,7392;
  -51,0385) e a área. Pedir isso para cada um dos 5.571 municípios exigiria 5.571 chamadas, então
  ele fica só como teste de conferência numa amostra.

## R4. Estações INMET

- **Decision**: catálogo de estações automáticas `https://apitempo.inmet.gov.br/estacoes/T`, com
  User-Agent de navegador (como registrado no REGISTRO). A busca é de vizinho mais próximo por
  distância de grande círculo, só entre as estações com `CD_SITUACAO = "Operante"`. As estações
  em pane aparecem só como informação.
- **Evidence**: HTTP 200, 261 KB, 0,6 s. São 668 estações (534 operantes, 134 em pane). A A025
  vem como RIO VERDE, GO, -17,78527777, -50,965, 780,11 m, operante desde 16/05/2007, o que confere
  com o REGISTRO.
- **Alternatives**: a lista de estações do portal BDMEP (mesma informação, menos estável).

## R5. Célula do NASA POWER

- **Decision**: grade de 0,5° de latitude por 0,625° de longitude, com centros em múltiplos
  inteiros do passo. Centro = (round(lat/0,5)·0,5; round(lon/0,625)·0,625).
- **Evidence** (contra o REGISTRO, que conferiu os centros pela igualdade dos 31 valores de
  jan/2025):
  - a estação A025 (-17,785; -50,965) dá (-18,0; -51,25), igual ao registrado;
  - o ponto antigo (-17,80; -50,92) dá (-18,0; -50,625), igual ao registrado.
- **Note**: a spec 002 confirma isso na própria fonte. Se a 002 encontrar divergência, a regra
  muda aqui e o teste FR-015 aponta.

## R6. Célula do IMERG

- **Decision**: grade de 0,1° com centros em x,x5. Centro = (floor(lat/0,1)·0,1 + 0,05;
  floor(lon/0,1)·0,1 + 0,05).
- **Evidence**: a A025 dá (-17,75; -50,95), igual ao centro registrado na pesquisa de chuva
  (`data/processed/pesquisa_chuva/cells.json`), a 4,23 km da estação.

## R7. Praças Conab

- **Decision**: lista de praças tirada dos nomes das abas ("Município-UF-Ano") das séries
  históricas de custo de soja, milho 2ª safra e sorgo, só dos anos 2025 e 2026. Cada praça é ligada
  a um código IBGE numa tabela de referência versionada, com correção manual das abreviações. A
  coordenada da praça é o centroide do município (R3).
- **Evidence**:
  - soja: 516 abas, 32 de 2025/26;
  - milho 2ª safra: 264 abas, 27 de 2025/26. URL sem `/view`: `.../agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls`;
  - sorgo: 54 abas, 6 de 2025/26 (Barreiras-BA, Rio Verde-GO, Uberaba-MG, Pedro Afonso-TO).
  - Os nomes trazem abreviações ("P. do Leste", "C. Novo do Parecis", "M. Cândido Rondon",
    "S. Luiz Gonzaga") e o prefixo "OGM-", por isso a correção manual.
- **Consequence**: o sorgo tem só 4 praças, então longe delas o aviso de praça distante é a regra.
  A spec 006 escolhe a praça por cultura; a 001 entrega a mais próxima no geral e a mais próxima
  de cada cultura.

## R8. Pilha técnica

- **Decision**:
  - Backend em Python 3.12 ou superior, com `uv` e FastAPI, testado com pytest e httpx (cliente de
    teste).
  - Frontend com Astro, Tailwind CSS e Leaflet para o mapa (tiles OpenStreetMap quando houver
    rede).
  - As versões exatas ficam presas no `uv.lock` e no `package-lock.json` e são conferidas na
    documentação oficial no momento da instalação.
- **Rationale**: é a decisão do time (Astro e Tailwind sairiam das specs) e o plano histórico já
  previa FastAPI e uv. Leaflet funciona sem chave de API.
- **Offline**: sem rede, o mapa mostra um fundo vazio com o contorno do Brasil (vindo de R2), e a
  busca e as coordenadas continuam funcionando (FR-014).

## R9. Distância e limites

- Distância de grande círculo (haversine, raio médio de 6.371,0088 km).
- O aviso de estação distante a 50 km é hipótese editável (spec). Fica em
  `referencias/localizacao/limites.json` com `"status": "hipotese"`.
