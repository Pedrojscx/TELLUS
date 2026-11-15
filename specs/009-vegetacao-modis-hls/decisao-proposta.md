# Proposta para D-007 (#69) — teste com amostra real

**Status**: PROPOSTA em teste. Não é decisão: quem fecha a #69 é o Maestro/usuário. No código e na
API todos os itens abaixo saem com `status: "hipotese"` (hipótese operacional do protótipo,
parametrizável em `referencias/vegetacao/parametros.json`). Nenhum é parâmetro científico validado.

**Pergunta (#69)**: qual índice, período mínimo e regra de qualidade respondem à pergunta de contexto da área?

## 1. Proposta (definida pelo usuário em 2026-11-15)

| Item | Proposta | Onde está no código |
|---|---|---|
| Produto | MODIS/Terra MOD13Q1 v061 (MYD13Q1 suportado, desligado) | `parametros.json` → `produtos_modis` |
| Índice | NDVI (EVI disponível por pedido) | `indice` |
| Série inicial | últimos 12 meses, contados da última composição publicada no cache | `janela_meses` |
| Mínimo provisório | 6 composições válidas; abaixo disso a série é `insuficiente`, sem preenchimento | `minimo_composicoes_validas` |
| Qualidade MODIS | regra do guia do produto (abaixo) | `regra_qualidade_modis` + `regras.valor_modis` |
| HLS | v2.0 com Fmask, complemento quando houver cena utilizável; sem cena ou credencial → `indisponivel` com motivo | `regra_qualidade_hls` + `servico.fonte_hls` |

## 2. Regra de qualidade aplicada e fonte

Documento: Didan, K.; Barreto Munoz, A. *MODIS Collection 6.1 (C61) Vegetation Index Product User
Guide* (MOD13 Series), **Version 3.10, setembro de 2019**, NASA LP DAAC —
<https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf>.

- **Seção 5.2, Tabela 1**: NDVI int16, faixa válida −2000 a 10000, preenchimento −3000, fator 0,0001;
  VI Quality uint16 (preenchimento 65535); pixel reliability int8 (preenchimento −1).
- **Seção 5.5.2, Tabela 4 (Pixel Reliability)**: −1 *Fill/No Data*; 0 *Good Data — Use with
  confidence*; 1 *Marginal data — Useful, but look at other QA information*; 2 *Snow/Ice*; 3 *Cloudy*.
- **Seção 5.5.2, Tabela 5 (VI Quality)**: bits 0–1 MODLAND (00 boa qualidade; 01 conferir outras
  QA; 10 provavelmente nuvem; 11 não produzido); bit 8 nuvem adjacente; bit 10 nuvens mistas;
  bit 14 possível neve/gelo; bit 15 possível sombra.

Aplicação (`backend/src/tellus/vegetacao/regras.py`, `valor_modis`):

1. Preenchimento ou fora da faixa válida → lacuna (fato do produto).
2. Rank 0 → valor.
3. Rank 1 → valor **só se** a VI Quality tiver MODLAND 00/01 e os bits 8, 10, 14 e 15 desligados;
   senão lacuna com o motivo do bit. *A escolha desses bits é hipótese do protótipo*: o guia manda
   "look at other QA information", mas não diz quais bits.
4. Rank 2, 3 e −1 → lacuna (`neve_gelo`, `nuvem`, `sem_dado`).

HLS: Ju, J. et al. *HLS Product User Guide*, **Product Version 2.0, atualizado em abril de 2026**,
<https://lpdaac.usgs.gov/documents/1698/HLS_User_Guide_V2.pdf> — **seção 6.4, Tabela 9**: bit 0 cirro
(reservado, não usado na v2.0), 1 nuvem, 2 adjacente a nuvem/sombra, 3 sombra, 4 neve/gelo, 5 água,
6–7 aerossol. Hipótese: bits 1–4 → lacuna; água (5) não rejeita.

## 3. Amostra real — Rio Verde-GO (ponto −17,785278; −50,965, estação A025)

**Acesso MODIS**: ORNL DAAC MODIS Web Service, `https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset`,
**sem login**. Lento (cerca de 48 s por pedido; no máximo 10 datas por pedido; a primeira tentativa,
às ~10h, deu timeout de 40 s). 12 pedidos (4 bandas × 3 blocos) + 1 de datas.

- Bruto: `data/raw/vegetacao/p_m17d785278_m50d965000/bruto/*.json`, cada um com `.meta.json` (URL,
  `obtido_em` 2026-11-15, sha256). Fora do Git (`.gitignore`: `data/raw/**`).
- Série derivada para a demo offline: `referencias/vegetacao/series/p_m17d785278_m50d965000/MOD13Q1.csv`
  + `.meta.json` (sha256 `08d76b8b…c5f6`, URLs, `sintetico: false`). Recriar:
  `cd backend && uv run python ../scripts/preparar_vegetacao.py --lat -17.785278 --lon -50.965 --meses 12 --exportar-referencia rio_verde_go`.
- Pixel: `h13v10.l3736.c0705`. O pixel calculado pela projeção senoidal (conta à mão em
  `tests/vegetacao/test_regras.py`) é o mesmo devolvido pela ORNL.

| Verificação | Resultado |
|---|---|
| Datas MOD13Q1 publicadas no ponto | 614; última composição 2026-10-16 (A2026289) |
| Cobertura dos últimos 12 meses | 23 composições, de 2025-11-01 a 2026-10-16, **nenhuma ausente** |
| Rank 0 (dado bom) | 18 |
| Rank 1 (marginal) | 4 — 3 passam pela VI Quality (2026-01-01, 2026-08-29, 2026-09-30); 1 rejeitada por possível sombra, bit 15 (2026-03-06) |
| Rank 3 (nuvem) | 1 (2025-12-03) |
| **Válidas pela regra** | **21 de 23** (só rank 0 daria 18) |
| Mínimo de 6 | **atingido** com folga, nas duas leituras (21 ou 18) |
| NDVI válido | de 0,4942 (2025-11-01) a 0,8358 (2026-02-02); pico em jan–fev e queda até set |

**HLS — teste no ponto (CMR, sem login, 2025-11-15 a 2026-11-15)**: HLSL30 v2.0, 84 grânulos (42
datas, tiles T22KDF e T22KEF), 29 com nuvem ≤ 20% no tile; HLSS30 v2.0, 329 grânulos (146 datas),
146 com nuvem ≤ 20% no tile. Catálogo bruto em `data/raw/vegetacao/hls_catalogo/` (com `.meta.json`).
A nuvem do catálogo é do tile inteiro, não do pixel: o uso real depende do Fmask no pixel.
**Acesso aos arquivos**: `data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/...` responde 302
para `urs.earthdata.nasa.gov` — **exige NASA Earthdata login**. Não baixei pixels HLS: (a) não li o
`.env` (Princípio VIII: agentes não leem `.env`); (b) o backend não tem leitor de GeoTIFF/COG.
Há cenas candidatas, mas **não verifiquei** se alguma é utilizável no pixel.

## 4. Compatibilidade com a spec 009

| Item | Situação com a proposta | Evidência |
|---|---|---|
| FR-001 MODIS e HLS como contexto histórico | atende; HLS como complemento opcional | `finalidade: contexto_historico`; `test_hls_sem_credencial_nao_bloqueia_modis` |
| FR-002 produto, versão, período, resolução, unidade, qualidade | atende em cada observação e indicador | `test_proveniencia_completa_em_toda_observacao_e_indicador` |
| FR-003 regra documentada de qualidade | atende, com fonte e seção; bits do rank 1 são hipótese | `test_valor_modis`, `test_marginal_consulta_vi_quality`, `test_rio_verde_ultimos_12_meses_sustenta_minimo` |
| FR-004 sem produtividade | atende | `test_nenhum_texto_de_produtividade_ou_previsao` |
| Cenário 1 (série e qualidade) | atende com dado real | `test_rio_verde_*` |
| Cenário 2 (nuvem → lacuna) | atende; 2 lacunas reais com motivo | idem |
| Edge Case HLS sem credencial | atende | `fontes[HLS].estado = indisponivel`, `motivo.codigo = sem_credencial` |
| SC-001 escala e limitação | atende (100% dos itens) | teste de proveniência |
| SC-002 | atende | varredura de termos |

## 5. Veredito

**SUSTENTA** como hipótese operacional do protótipo para Rio Verde-GO: a janela de 12 meses tem as
23 composições esperadas, 21 passam na regra do guia (18 só com rank 0) e o mínimo de 6 é atingido
com folga. O HLS fica como complemento `indisponivel` até haver credencial e leitor de COG, sem
bloquear.

## 6. Limitações (não resolvidas aqui)

- **Uma amostra, um pixel, uma safra**: o resultado vale para o ponto da A025 em 2025-11 a 2026-10.
  Em outra região ou ano mais nublado, 12 meses podem dar menos de 6 válidas; a resposta então
  diz `insuficiente`, sem preencher.
- **Mínimo de 6 e janela de 12 meses não têm fonte científica**: são escolha do protótipo. Seis
  composições de 16 dias cobrem cerca de 3 meses: não bastam para descrever uma safra inteira.
- **Bits consultados no rank 1** (8, 10, 14, 15): hipótese; o guia não fixa quais.
- **Pixel de 250 m ≠ lavoura** e não foi feita comparação com verdade de campo.
- **Polígono**: o serviço agrega por pixel com pesos, mas o script só prepara ponto.
- **HLS**: falta pixel real; o formato do cache HLS e a regra Fmask só foram testados com fixture sintética.
- ORNL lenta e instável; a demo usa a série versionada (o aviso traz a data de obtenção).

## 7. O que a decisão precisa registrar ao fechar a #69

Aprovar ou trocar cada item da tabela 1; dizer se o mínimo vale por janela ou por estação de
cultivo; dizer se o rank 1 entra (e com quais bits); dizer se o HLS entra só com credencial.
Impacto: muda apenas `parametros.json` (status `hipotese` → valor aprovado com fonte); o código não muda.
