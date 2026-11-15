# Implementation Plan: Vegetação MODIS e HLS

**Branch**: `009-vegetacao-modis-hls` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)
**Issues**: #50 (US-009), #51 (T-024), #91 (T-060), #92 (T-061), #69 (T-038 / D-007, decisão)

## Summary

Contexto histórico de cobertura vegetal da área confirmada (ou de um ponto): série NDVI/EVI do
MODIS MOD13Q1 v061 (MYD13Q1 opcional) e, quando houver cache, HLS v2.0. Cada observação e cada
indicador levam a proveniência completa e os avisos de escala e limitação. Dado sem qualidade vira
lacuna explícita. HLS sem credencial ou sem cache fica `indisponivel` com motivo e não bloqueia.
Nada é convertido em colheita (FR-004).

Os pontos da decisão D-007 (#69) entram como **hipótese operacional do protótipo** (status
`hipotese`, parametrizáveis em `referencias/vegetacao/parametros.json`): MOD13Q1, NDVI, janela dos
últimos 12 meses, mínimo de 6 composições válidas, regra de QA do guia do produto. Ver
[decisao-proposta.md](decisao-proposta.md).

## Technical Context

- **Language/Version**: Python ≥ 3.12, uv, FastAPI; pacote `tellus` em `backend/src/`.
- **Dependências**: nenhuma nova. `httpx` (já usado em `tellus.clima.imerg`) só no script de preparação.
- **Storage**: cache em `data/raw/vegetacao/<chave_area>/` (fora do Git); série derivada da demo em
  `referencias/vegetacao/series/<chave_area>/` (versionada, com `FONTE.md`).
- **Testing**: pytest; fixtures **sintéticas** marcadas (`"sintetico": true` → aviso `dado_sintetico`).
- **Constraints**: motor puro (Princípio VI); mesma resposta para o mesmo cache (III); sem token
  em resposta, cache ou referência (VIII).

## Constitution Check

| Princípio | Como é atendido |
|---|---|
| I Rastreabilidade | todo item com `valor` em `fontes[*].serie` e `fontes[*].indicadores` traz produto, versão, DOI, período, resolução, unidade, qualidade, área, escala, limitação, origem e status; `test_proveniencia_completa_em_toda_observacao_e_indicador` percorre a resposta |
| II Sem parâmetro inventado | fatos de produto com fonte em `produtos.json`; regras de uso com `status: hipotese` em `parametros.json`, repetidas em cada item |
| III Reprodutibilidade | janela relativa à última data do cache, não ao relógio; `test_determinismo_mesmo_pedido_mesmo_cache`; hash do CSV conferido (`cache_alterado`) |
| IV Escala | `escala` e `limitacao` em cada item; aviso global de 250 m / 30 m; varredura de termos proibidos |
| VI Motor puro | `vegetacao/regras.py` sem rede (teste bloqueia socket), casos à mão (pixel senoidal, NDVI/EVI, agregação) |
| VII Degradação | fonte sem cache → `indisponivel` com motivo; nenhuma fonte → 404 com `origem` nomeando os produtos |
| VIII Segredos | `EARTHDATA_TOKEN` só por ambiente; teste garante que não volta na resposta |

## Project Structure

```text
backend/src/tellus/vegetacao/
  regras.py       # puro: grade senoidal, calendário 16 dias, QA MODIS/Fmask, agregação, sazonalidade
  servico.py      # leitura do cache, proveniência, suficiência, degradação, resposta
  modis_ornl.py   # cliente ORNL DAAC MODIS Web Service (só o script usa)
backend/src/tellus/api/vegetacao.py   # GET/POST /api/vegetacao/contexto
backend/tests/vegetacao/              # regras, serviço, API (fixtures sintéticas)
referencias/vegetacao/                # produtos.json, parametros.json, FONTE.md, series/
scripts/preparar_vegetacao.py         # baixa MOD13Q1 da ORNL e grava bruto + série
```

## Contrato (resumo)

- `GET /api/vegetacao/contexto?lat&lon[&indice=ndvi|evi][&inicio&fim]`
- `POST /api/vegetacao/contexto` `{geometria, id_geometria, indice?, inicio?, fim?}` — `id_geometria`
  tem de bater com a geometria (mesma regra da confirmação da spec 002).
- Resposta: `finalidade`, `area`, `indice`, `periodo_pedido`, `parametros` (todos com status),
  `fontes[]` (`produto`, `estado` disponivel|indisponivel, `motivo`, `origem`, `area` com pixels e
  pesos, `serie[]`, `suficiencia`, `indicadores[]`), `avisos[]`.
- Erro: `{"erro": {"codigo", "mensagem", "origem", "campo"}}`.

## Fora deste plano

- Exibição na interface (spec 012).
- Download de HLS: exige Earthdata login e leitura de GeoTIFF (COG); o backend não tem leitor. O
  serviço já lê um cache HLS no formato definido (`data,sensor,granulo,pixel,azul,vermelho,nir,fmask`).
- Polígono no script de preparação (o serviço já agrega por pixel com pesos; o script só faz ponto).
