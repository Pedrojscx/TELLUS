# Mapa das specs

Ordem combinada em 14/11, seguindo os labels `area:*`. Antes de criar uma spec, confira aqui se o
número já está reservado. Ao criar, mude o status e anote a branch.

| Nº | Spec | Label | Depende de | Status |
|---|---|---|---|---|
| 001 | localizacao: local em qualquer ponto do Brasil, com as referências (POWER, IMERG, INMET, Conab, IBGE) | area:localizacao | — | spec escrita (`001-localizacao`) |
| 002 | dados-clima: POWER (temperatura, radiação, umidade, vento), IMERG e INMET para chuva, cache | area:dados-clima | 001 | reservada |
| 003 | zarc: janelas e risco por cultura, grupo e solo, via SISZARC | area:zarc | 001 | reservada |
| 004 | solo-culturas: água disponível, Kc, Ky e fases de milho, sorgo e cobertura, com fonte | area:solo-culturas | — | reservada |
| 005 | motor-hidrico: ETo FAO-56, balanço diário, perda de produtividade FAO-33 | area:motor-hidrico | 002, 004 | reservada |
| 006 | economia: custo Conab, preço, margem em três cenários | area:economia | 001, 005 | reservada |
| 007 | recomendacao: três opções lado a lado, com ZARC ao lado | area:recomendacao | 003, 005, 006 | reservada |
| 008 | api: contrato único entre motor e interface | area:api | 001 a 007 | reservada |
| 009 | web: fluxo único no navegador | area:web | 008 | reservada |
| 010 | design: identidade visual e componentes | area:design | — | reservada |
| 011 | vegetacao: NDVI MODIS como contexto (extra) | area:vegetacao | 001 | extra, depois do fluxo |
| 012 | umidade-solo: umidade do solo por satélite (extra) | area:umidade-solo | 001 | extra, depois do fluxo |

`area:infra` é transversal (ambiente, um comando para iniciar, cache) e entra no plano de cada spec.
