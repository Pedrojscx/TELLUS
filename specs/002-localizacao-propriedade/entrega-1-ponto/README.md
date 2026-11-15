# Entrega 1 da spec 002: ponto e referências do local

Esta pasta era a `specs/001-localizacao` do LK, escrita e implementada em paralelo ao plano
oficial em 14/11. Ela foi integrada como a primeira entrega da
[spec 002-localizacao-propriedade](../spec.md).

## O que esta entrega cobre da spec 002

- **"Marcação" do FR-001**: um ponto escolhido por busca de município, por coordenadas ou por
  clique no mapa.
- **Município associado (FR-003)**, com código IBGE.
- **Referências do local, que as specs 003, 004 e 007 consomem**: célula POWER, célula IMERG,
  estação INMET mais próxima, praça Conab mais próxima (no geral e por cultura) e município do
  ZARC.

## O que falta para fechar a spec 002

- Desenho de polígono e upload de KML, KMZ, GeoJSON e Shapefile .zip (FR-001), validação de
  geometria (FR-002), área e todos os municípios atingidos (FR-003), corrigir ou substituir
  (FR-004).
- Consulta pelo CAR (depende da spec 001-pesquisa-car-wfs).
- **Rastreabilidade completa (Princípio I da constituição 1.1.0)**: hoje cada referência traz
  fonte, url, data, localização e distância. Faltam `versao` do produto, `periodo` e `qualidade`
  em cada registro de proveniência, e o teste automático que percorre a resposta.

## Onde está o código

- `backend/src/tellus/localizacao/` (regras puras, serviço, busca) e
  `backend/src/tellus/api/localizacao.py`
- `referencias/localizacao/`, gerado por `scripts/preparar_localizacao.py`
- `frontend/src/components/SeletorLocal.astro` e `ReferenciasLocal.astro`
- Testes: `backend/tests/localizacao/` e `backend/tests/api/` (50 passando)
