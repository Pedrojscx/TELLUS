# Sincronia LK → Pedro (14/11/2026, 23h40)

Cole o texto abaixo na sua sessão (Claude Code ou Codex) depois de `git pull origin main`.

---

Você está no repositório TELLUS (NASA Space Apps 2026, desafio Field Shift, prazo dom 15/11 às
12h BRT). Enquanto você estava sem limite, o LK e o Claude Code dele trabalharam em paralelo, sem
ver a sua branch `sdd/etapa-1`. Já está tudo reconciliado na `main`. Antes de agir, leia:
`.specify/memory/constitution.md`, `docs/sdd/MAPA_FEATURES.md`,
`specs/002-localizacao-propriedade/entrega-1-ponto/README.md` e o fim do `REGISTRO.md`.

## O que foi decidido na reconciliação

1. **Seu plano é o oficial.** A `sdd/etapa-1` foi mergeada na `main`: as 13 specs, o
   `MAPA_FEATURES.md`, as dúvidas, a extensão github e as issues continuam valendo, com a mesma
   numeração.
2. **Constituição 1.1.0.** É a sua (9 princípios) mais a seção "Decisões de Dados e Escopo":
   - a chuva do POWER nunca entra no balanço;
   - cobertura nacional, com a referência mais próxima e sua distância declaradas, ou a lacuna
     declarada;
   - escopo até o prazo: o fluxo funcional vem antes de vegetação, SMAP e identidade visual.
3. **O trabalho do LK virou a entrega 1 da sua spec 002-localizacao-propriedade.** A pasta
   ficou em `specs/002-localizacao-propriedade/entrega-1-ponto/`. O código está pronto e testado:
   - o ponto vem por busca de município, coordenadas ou clique no mapa;
   - o local é resolvido para o município e código IBGE, a célula POWER, a célula IMERG, a estação
     INMET operante mais próxima, a praça Conab mais próxima (no geral e por cultura) e o
     município do ZARC, cada um com fonte e distância.
4. **As specs 002 a 007 do LK** (branches `002-dados-clima` … `007-recomendacao`) ficam só como
   consulta. A tabela de equivalência está em `docs/sdd/MAPA_SPECS.md`. Elas têm detalhes que
   podem enriquecer as suas:
   - números de conferência de Rio Verde (RELATORIO de chuva, portarias ZARC por grupo, custos
     Conab);
   - a regra de ordenação "maior margem no cenário conservador";
   - a braquiária solteira como cobertura.
5. **Pilha e estrutura fixadas pelo código que já existe** (siga nas próximas specs):
   - backend Python ≥ 3.12 com `uv` e FastAPI em `backend/` (pacote `tellus`, layout `src/`);
   - frontend Astro 7, Tailwind 4 e Leaflet em `frontend/`;
   - código em `backend/src/tellus/<area>/` (`regras.py` puro, `servico.py`), rotas em
     `backend/src/tellus/api/<area>.py`, testes em `backend/tests/<area>/`;
   - referências versionadas em `referencias/<area>/` com `FONTE.md`, geradas por
     `scripts/preparar_<area>.py`;
   - brutos em `data/raw/<area>/` (fora do Git, só os `.meta.json` entram).
6. **Commits do LK** saem só com o nome dele, sem `Co-Authored-By` de IA nem rodapé de ferramenta.

## Achados de dados (testados em 14/11, 22h50)

- IBGE: lista com 5.571 municípios e malha mínima com 5.570 polígonos. Boa Esperança do Norte-MT
  (5101837) ainda não tem polígono.
- INMET `apitempo.inmet.gov.br/estacoes/T` (com User-Agent de navegador): 668 estações
  automáticas, 534 operantes. A A025 confere com o REGISTRO.
- Conab: a planilha de milho 2ª safra fica em
  `.../agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls` (o link da página termina
  em `/view` e devolve HTML). São 27 praças com planilha de 2025/26. **Sorgo só em 4**:
  Barreiras-BA, Rio Verde-GO, Uberaba-MG e Pedro Afonso-TO. Isso afeta a spec 007.
- Células: POWER = round(lat/0,5)·0,5 e round(lon/0,625)·0,625; IMERG = centro da célula de
  0,1°. As duas conferem com o REGISTRO. Em Rio Verde, a célula POWER fica a 38 km do ponto.

## O que falta na 002 (ainda sem dono)

- Desenho de polígono, upload (KML, KMZ, GeoJSON, Shapefile .zip), validação, área e municípios
  atingidos.
- Consulta pelo CAR (depende da 001-pesquisa-car-wfs).
- Rastreabilidade completa do Princípio I: faltam `versao`, `periodo` e `qualidade` nos registros
  de proveniência, e o teste que percorre a resposta.

## Divisão proposta

- **LK + Claude**: 003 dados-clima agora, que é o caminho crítico (003 → 006 → 007 → 008). A D-002
  (lacuna do IMERG depois de set/2025) segue a recomendação do DUVIDAS: recusar a lacuna até haver
  fonte e regra validada.
- **Pedro**: 004 calendario-zarc (a sequência do SISZARC está no REGISTRO) e 005 base-solo-culturas.
  As duas não dependem da 003.
- **Sem dono por enquanto**: 001 pesquisa CAR e o resto da 002. O cunhado do Pedro mandou
  car.gov.br, geo.cati.sp.gov.br e datageo.ambiente.sp.gov.br. Só o CAR serve para Rio Verde; os
  outros dois são de SP.
- Fluxo por spec: crie a branch `NNN-nome` a partir da `main`, depois `/speckit-plan`,
  `/speckit-tasks` e `/speckit-implement`. Só faça merge na `main` com os portões da constituição
  passando. Marque na issue quem pegou, atualize o `MAPA_FEATURES.md` e escreva no `REGISTRO.md`.
