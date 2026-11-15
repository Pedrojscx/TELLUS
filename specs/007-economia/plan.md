# Implementation Plan: Economia

**Branch**: `007-economia` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Summary

A margem por hectare sai nos cenários conservador, central e favorável:

`margem = produtividade de referência Conab × (1 − perda do cenário) ÷ 60 × preço − custo do nível`

- **Perda**: os quantis da simulação hídrica (006).
- **Custo**: a planilha Conab da praça mais próxima que tenha a mesma cultura, com a distância.
  Mostra todos os itens, o mês, o sistema e a unidade, e recompõe os totais. O nível padrão é o
  custo operacional, e o produtor pode trocar.
- **Preço**: milho pelo Indicador CEPEA/ESALQ; sorgo indisponível sem fonte (D-005); cobertura sem
  receita.

Toda premissa é editável, e a resposta mostra a margem anterior e a nova.

## Technical Context

**Language/Version**: Python ≥ 3.12, módulo `tellus.economia`

**Primary Dependencies**: xlrd (já usado). O XLS do CEPEA exige `ignore_workbook_corruption`: a
tabela de alocação OLE é inconsistente, mas o conteúdo é íntegro

**Storage**:
- `referencias/economia/conab_{milho_2a_safra,sorgo,soja}.json`: as 65 planilhas de 2025/26 já
  lidas, com itens, totais e divergências (zero);
- `referencias/economia/cepea_milho.json`: série desde 2024;
- todos gerados por `scripts/preparar_economia.py`.

**Testing**: pytest, com recomposição de todas as planilhas, margem à mão e edição com antes e depois

## Constitution Check

| Princípio | Como cumpre | Situação |
|---|---|---|
| I. Rastreabilidade | Custo com praça, distância, planilha, mês, sistema, itens e arquivo (sha256). Preço com indicador, praça, data, unidade e url. `versao_premissas` | ok |
| II. Sem parâmetro inventado | Sorgo sem preço = indisponível (sem margem factual). Cobertura sem custo = indisponível. Percentis = hipótese declarada | ok |
| III. Reprodutibilidade | Referências versionadas; a mesma entrada dá a mesma margem | ok |
| IV. Escala | A produtividade da Conab é ex-ante; o preço é de Campinas (nota) | ok |
| V. Premissas editáveis | preço, produtividade, nível de custo, cada item de custo, custo total e percentis; `alteracoes` e `comparacao` | ok |
| VI–IX | Cálculo puro sobre as referências; sem credencial | ok |

## Project Structure

```text
backend/src/tellus/economia/{conab.py, servico.py}
backend/src/tellus/api/economia.py   # POST /api/economia/margem, GET /api/economia/praca
backend/tests/economia/test_economia.py
referencias/economia/{conab_*.json, cepea_milho.json}
scripts/preparar_economia.py
```

## Complexity Tracking

Sem violações.
