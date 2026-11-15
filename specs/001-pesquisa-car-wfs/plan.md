# Implementation Plan: Pesquisa CAR WFS

**Branch**: `001-pesquisa-car-wfs` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

O produtor informa o número do CAR e o sistema consulta o WFS público do SICAR.
- Se achar o imóvel, devolve um **candidato a lavoura**: polígono, área em hectares, municípios
  atingidos, condição no CAR e proveniência. O candidato fica `aguardando_confirmacao` até o
  produtor confirmar.
- Se não achar, o estado diz por quê (`codigo_invalido`, `inexistente`, `sem_geometria` ou
  `fonte_indisponivel`) e oferece o upload do shapefile exportado do SICAR, que passa pela mesma
  validação.

A validação de geometria e o resumo territorial (área e municípios) ficam num módulo puro,
reaproveitado pela spec 002 para desenho e upload genérico.

## Technical Context

**Language/Version**: Python ≥ 3.12, no mesmo pacote `tellus`

**Primary Dependencies**: httpx (WFS); pyshp 3.1 (leitura de shapefile em Python puro, sem GDAL)

**Storage**: cache das respostas WFS em `data/raw/car/<codigo>.json` com `.meta.json` (fora do Git)

**Testing**: pytest, com respostas WFS gravadas (fixture) e rede bloqueada nas regras

**Project Type**: aplicação web (módulo `tellus.car`, rotas, campo na tela)

**Performance Goals**: consulta em menos de 2 s com rede (o WFS respondeu em 0,35 s); validação
de um polígono de até 5 mil vértices em menos de 1 s

**Constraints**:
- não inventa geometria;
- geometria inválida nunca vira área de cálculo;
- confirmação explícita;
- nenhum dado pessoal (o WFS não traz proprietário).

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | A consulta registra código, data, fonte, versão (camada e serviço WFS 2.0), resultado e qualidade (condição e data de atualização no CAR) | ok |
| II. Sem parâmetro inventado | Não há parâmetro agronômico. A tolerância de validação fica em `referencias/car/limites.json` com status | ok |
| III. Reprodutibilidade | O mesmo código com o mesmo cache dá a mesma resposta. O bruto é recriado pela própria consulta, e o `.meta.json` traz url, data e sha256 | ok |
| IV. Escala | A área vem do CAR declarado, com o aviso "limite declarado, não medido" | ok |
| V. Premissas | n/a | n/a |
| VI. Puro | `tellus.car.regras` (formato do código, validação, área, municípios) é puro, com caso à mão de área e validação | ok |
| VII. Degradação | Fonte fora do ar: usa o cache com aviso e data. Sem cache: estado `fonte_indisponivel` com a origem, mais a alternativa de upload | ok |
| VIII. Segredos | Sem credencial | ok |
| IX | Branch própria, PT-BR | ok |

## Project Structure

```text
backend/src/tellus/car/
├── regras.py     # puro: normalizar/validar código, validar polígono, área (ha), municípios atingidos
├── wfs.py        # cliente WFS SICAR + cache
├── shapefile.py  # leitura do .zip do SICAR (pyshp), exige coordenadas geográficas
└── servico.py    # consulta → estado + candidato; upload → candidato; confirmar → lavoura
backend/src/tellus/api/car.py      # GET /api/car/{codigo}, POST /api/car/upload, POST /api/lavoura/confirmar
backend/tests/car/
referencias/car/limites.json
frontend/src/components/ConsultaCar.astro
```

**Structure Decision**: mesmo padrão das specs 002 e 003. `regras.validar_poligono` e
`regras.resumo_territorial` são a base da 002 (desenho e upload genérico) e ficam públicas.

## Complexity Tracking

Sem violações.
