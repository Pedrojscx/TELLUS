# Retorno da etapa 1 de SDD

Data: 2026-11-14. Spec Kit: 1.4.0. Branch de trabalho: `sdd/etapa-1`.

## O que foi feito

1. Conferido o estado do Git antes de editar: `git status --short --branch` e
   `git log -5 --format=fuller`.
2. Consultado o grafo existente com `graphify query` antes de navegar no repositório.
3. Iniciado `graphify .` com as exclusões de `.graphifyignore`; a extração estrutural completou
   279 nós e 648 relações. A extração semântica não terminou por limite de uso do agente.
   Depois, `graphify update .` atualizou o grafo estrutural para 1.085 nós e 1.313 relações.
4. Lidos `docs/sdd/RETORNO_INSTALACAO.md`, `REGISTRO.md`,
   `docs/pesquisa_chuva/RELATORIO.md`, `data/raw/zarc/FONTE.md`,
   `data/raw/conab/FONTE.md` e `Pesquisa_NASA_Agricultura_Agentes.md`.
   `docs/PLANO.md` foi usado somente para método histórico.
5. Aplicado o fluxo de `speckit-constitution`: constituição em
   `.specify/memory/constitution.md`.
6. Criados o mapa, a base de referência e 13 specs na ordem definida no mapa. Cada spec passou
   por triagem de ambiguidade do fluxo `speckit-clarify`; as dúvidas ficaram sem resposta e foram
   preservadas nos arquivos e no registro central.
7. Rodada a autoverificação com `rg`: 61 requisitos funcionais e 27 critérios de sucesso;
   nenhum nome de framework ou biblioteca aparece nas specs.

## Constituição

Versão 1.0.0, com nove princípios: rastreabilidade; sem parâmetro inventado;
reprodutibilidade; respeito à escala; premissas editáveis; motor puro; degradação explícita;
segredos fora do Git; e regras de stack, idioma e trabalho. Cada princípio tem regra verificável.
O documento também exige contrato versionado, dados brutos recriáveis e confirmação humana para push.

## Features

| ID | Nome | Spec | Dependências | Requisitos | Dúvidas |
|---|---|---|---|---:|---:|
| 001 | pesquisa-car-wfs | `specs/001-pesquisa-car-wfs/spec.md` | — | 4 | 1 |
| 002 | localizacao-propriedade | `specs/002-localizacao-propriedade/spec.md` | 001 opcional | 5 | 0 |
| 003 | dados-clima | `specs/003-dados-clima/spec.md` | 002 | 5 | 1 |
| 004 | calendario-zarc | `specs/004-calendario-zarc/spec.md` | 002 | 5 | 0 |
| 005 | base-solo-culturas | `specs/005-base-solo-culturas/spec.md` | 004 | 5 | 1 |
| 006 | motor-hidrico-entressafra | `specs/006-motor-hidrico-entressafra/spec.md` | 003, 004, 005 | 5 | 1 |
| 007 | economia | `specs/007-economia/spec.md` | 002, 005, 006 | 5 | 1 |
| 008 | recomendacao | `specs/008-recomendacao/spec.md` | 004, 006, 007 | 5 | 1 |
| 009 | vegetacao-modis-hls | `specs/009-vegetacao-modis-hls/spec.md` | 002 | 4 | 1 |
| 010 | umidade-smap | `specs/010-umidade-smap/spec.md` | 002 | 4 | 1 |
| 011 | contrato-api | `specs/011-contrato-api/spec.md` | 002–010 | 5 | 1 |
| 012 | interface-web | `specs/012-interface-web/spec.md` | 011 | 5 | 1 |
| 013 | identidade-visual | `specs/013-identidade-visual/spec.md` | 012 | 4 | 1 |

## Decisões de interpretação

- Rio Verde/GO é só o caso de validação, não prova nacional.
- CAR é caminho opcional; desenho e upload não dependem de WFS.
- Pousio é manejo, não cultura com janela inventada. Cobertura sem ZARC aplicável não recebe
  recomendação como se tivesse janela oficial.
- IMERG Final V07 é a chuva principal. INMET valida localmente. Chuva POWER não entra no cálculo.
- O catálogo consultado acaba em set/2025; a lacuna recente bloqueia resultado que a contenha.
- FAO-56 e FAO-33 são métodos. Não fornecem parâmetros locais por si.
- As duas metodologias da recomendação usam o mesmo motor e as mesmas entradas.
- Vegetação e SMAP são contexto opcional; não definem produtividade nem substituem o cálculo.

## Dúvidas

Há 11 dúvidas em [DUVIDAS_ETAPA1.md](DUVIDAS_ETAPA1.md). Elas bloqueiam somente o trecho citado,
não a leitura e revisão das demais specs.

## Autoverificação

- Nenhuma spec cita framework ou biblioteca.
- Os 27 critérios de sucesso são mensuráveis.
- Parâmetros agronômicos e econômicos não receberam números sem fonte. A
  [base de referência](BASE_REFERENCIA_SOLO_CULTURAS.md) deixa os campos pendentes explícitos.
- A spec de recomendação exige o mesmo motor para as duas metodologias.
- IMERG, INMET, POWER, ZARC, Conab, CEPEA/ESALQ, MODIS, HLS, SMAP, CAR e os casos de borda estão
  nas specs correspondentes.
- As checklists das specs com dúvida mantêm a pendência aberta.

## Desvios

- A extração semântica completa do `graphify .` não terminou porque o agente atingiu limite de uso.
  A extração estrutural terminou e `graphify update .` atualizou os arquivos do grafo; eles são
  ignorados pelo Git.
- Não criei branches por feature. As 13 specs foram criadas diretamente em `sdd/etapa-1`, como
  permite o objetivo de manter tudo numa branch visível.
- Não foram criados commits nem push: a orientação vigente do responsável humano é fazer commits
  e push pessoalmente. Não abri issues.

## Estado do Git

- Branch: `sdd/etapa-1`.
- Commit base: `cb79f55185ff3331e954cb4fe5c9687e66971577`.
- Commit desta etapa: pendente do responsável humano.
- Push desta etapa: não feito.

Retorno salvo em docs/sdd/RETORNO_ETAPA1.md. Volte à conversa de planejamento para a revisão.
