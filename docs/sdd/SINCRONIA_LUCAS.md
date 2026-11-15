# Sincronia Pedro → LK (15/11/2026, 02h40)
Cole o texto abaixo na sua sessão (Claude Code ou Codex).
---
Você está no repositório TELLUS (NASA Space Apps 2026, desafio Field Shift, prazo dom 15/11 às
12h BRT). Enquanto você fazia 004 a 008, o Pedro integrou várias specs na `main`. Você já integrou a
008 por cima delas (`135e0ac`, `7583eb2`, `84f0129`); esta nota registra o que veio do lado do Pedro e o que falta.

**Antes de agir:** rode `git pull origin main` e leia nesta ordem: `.specify/memory/constitution.md`,
este arquivo e o fim do `REGISTRO.md`.

Estado conferido:
- `main` em **`84f0129`** (15/11, com a sua 008 integrada);
- `cd backend && uv run pytest -q` → **442 passed, 1 skipped**. O skip é `tests/zarc/test_rio_verde.py`, que pula quando o XLS do SISZARC não está na máquina;
- `cd frontend && npm run build` → OK, 1 página;
- 110 issues: 88 fechadas e 22 abertas. O Project 18 está consistente: nenhuma issue fechada fora de Done e nenhuma aberta em Done.

## 1. O que entrou na main desde a sua última sincronia

| Spec | Commits | Issues fechadas | O que faz |
|---|---|---|---|
| 009 vegetação | `c566735`, `56fcf9c` | #69, #91, #92, #109 | `tellus.vegetacao` + `GET/POST /api/vegetacao/contexto`. MOD13Q1 v061 NDVI só como contexto histórico, com proveniência, escala e limite em cada valor. Nuvem ou QA ruim vira lacuna. HLS é opcional e não bloqueia. Série real de Rio Verde em `referencias/vegetacao/`. |
| 010 umidade SMAP | `fee2a68`, `3e09ced`, `a0dd976`, `bc39dbd` | #70, #93, #94 | `tellus.umidade` + `/api/umidade/{produtos,contexto}`. SPL3SMP_E como contexto regional, com aviso de escala em 100% dos valores. Célula sem dado fica indisponível, sem vizinho. Série real versionada em `referencias/umidade/rio_verde_go/`. |
| integração 009/010 | `db9cac1`, `2ed25ac` | — | Rotas registradas no `app.py`; D-007 e D-008 no `DUVIDAS_ETAPA1.md`. |
| 011 contrato da API | `ba91643`, `4937cf3`, `4bc0647` | #55, #96, #97, #98, #99, #71 | `tellus.contrato` versão 1.0.0. Pedido validado e resposta rastreável com a saída real da 006 e da 007. Formato único de erro. Contextos 009/010 opcionais, sem efeito no resultado principal (teste com séries reais). Limites da D-009 num arquivo único. |
| 002 entrega 2 (área) | `1453f5e`, `cb33b2e`, `a2cf3cb` | #19, #20, #21, #22, #24, #30, #31, #32 | `tellus.lavoura` + `/api/lavoura/{arquivo,desenho,limites}`. KML, KMZ, GeoJSON e Shapefile .zip só com a stdlib. Desenho no mapa em Leaflet puro, testado manualmente pelo Pedro. Erros nomeados. Confirmação obrigatória nos seis modos. O mesmo `id_geometria` em todos os formatos. |
| #35 chuva por área | `d3b52bd`, `5569f55`, `cd4d6b8` | #35 | Média ponderada pela fração de área das células IMERG de 0,1°, ligada ao serviço (`POST /api/clima/{serie,resumo}`) e ao motor. Célula sem dado deixa o dia indisponível, sem renormalizar. |
| docs 003 | `5a1871e` | — | Resposta da D-002 registrada no `DUVIDAS` (estava aplicada no `research.md` R2, mas sem registro) e checklist da 003 completo. |

**Pendente de merge** (não está na `main`):
- **012 interface web:** plano, adaptador provisório e 7 telas em `/comparacao` com dados de exemplo identificados por um selo, mais 124 testes vitest das regras puras. Vai ser publicada logo depois desta nota na branch `origin/012-interface-web`, **sem merge na `main`**, já atualizada sobre `84f0129`. A integração com a API espera a #54 (a 008 na seção do contrato).

## 2. Decisões tomadas

| ID | Valor | Status | Issue | Onde está |
|---|---|---|---|---|
| D-007 | MODIS MOD13Q1 v061, NDVI, últimos 12 meses, mínimo de 6 composições válidas. QA do guia MOD13 C6.1 v3.10 §5.5.2 (Tab. 4 e 5): rank 0 aceito, rank 1 condicional, o resto vira lacuna. Teste real em Rio Verde (ORNL, sem login): 21 de 23 composições válidas. HLS real fica para depois da demo. | hipótese operacional | #69 (fechada); HLS na #51 (aberta) | `docs/sdd/DUVIDAS_ETAPA1.md`, `referencias/vegetacao/parametros.json`, `specs/009-vegetacao-modis-hls/decisao-proposta.md` |
| D-008 | SMAP SPL3SMP_E V006 (9 km, m³/m³), observações válidas pelo bit 0 da `retrieval_qual_flag` nos últimos 30 dias. Amostra real (Earthdata), de 2026-10-17 a 11-15, célula L1059/C1382 a 5,4 km de Rio Verde: 27 de 30 dias com arquivo, 17 válidas em 12 dias, faixa de 0,19 a 0,36 m³/m³. | hipótese operacional | #70 (fechada) | `DUVIDAS`, `specs/010-umidade-smap/decisao-proposta.md` |
| D-009 | Detalhes abaixo da tabela. | hipótese operacional, revisável depois da demo | #71 (fechada) | `backend/src/tellus/contrato/limites.json`, `DUVIDAS`, `specs/011-contrato-api/decisao-proposta.md` |
| D-002 | Recusar a lacuna do IMERG Final depois de 2025-09-30: `nao_publicado` + aviso `lacuna_imerg`, sem trocar por Late/Early. | decidida, por você | #34 (fechada) | `DUVIDAS` (`5a1871e`) |
| Formato de erro | `{"erro": {codigo, mensagem, origem, campo}}` em todos os handlers do `app.py` e em `/api/umidade`. | decidido | #98 (fechada) | `backend/src/tellus/api/app.py` (`4bc0647`) |
| Testes de frontend | Só vitest e só nas regras puras (`validacao.ts`, `etapas.ts`, `premissas.ts`), sem teste de componente ou navegador. | decidido | #56 | branch `012-interface-web` (pendente de merge) |

Valores da D-009, todos em `backend/src/tellus/contrato/limites.json`:
- `arquivo_max_bytes` = 20 MB, para todos os formatos;
- `vertices_total_max` = 10.000;
- `vertices_por_anel_max` = 5.000, o limite técnico da sua spec 001;
- `area_max_ha` = 100.000;
- `processamento_prazo_s` = 60, síncrono e sem fila;
- uma lavoura por envio.

O teto de 10.000 vértices veio da medição do pior caso (polígono em dente de serra, O(n²)): 10,2 s com 5.000 vértices, 21,9 s com 10.000 e 43,8 s com 20.000. Os tempos são da máquina do Pedro; meça de novo no servidor da demo.

## 3. ⚠️ MUDANÇAS NO SEU CÓDIGO

1. **CAR (spec 001): mesmos valores, mesmo comportamento.** Os 5.000 vértices por anel e os 20 MB do upload agora são lidos do arquivo único `backend/src/tellus/contrato/limites.json` (chaves `vertices_por_anel_max` e `arquivo_max_bytes`).
   - Arquivos alterados em `ba91643`: `backend/src/tellus/car/servico.py`, `backend/src/tellus/car/regras.py` (o padrão de `validar_poligono` deixou de ser 5000 fixo), `backend/src/tellus/api/car.py` e `referencias/car/limites.json` (saiu `max_vertices_anel`; `casas_decimais_id` continua).
   - Os testes de `tests/car/` passaram sem alteração.
   - O teste `tests/contrato/test_limites.py::test_um_unico_arquivo_define_os_limites` falha se outro arquivo voltar a definir esses números.
   - Aviso também na #1.
2. **Motor (spec 006):** `backend/src/tellus/motor/servico.py` ganhou 6 linhas e perdeu 4 em `d3b52bd` (#35), com autorização do Pedro.
   - `_serie_com_eto(lat, lon, geometria=None, id_geometria=None)` usa a série por área quando há geometria.
   - `preparar()` guarda `geometria` e `id_geometria` do pedido.
   - `simular()` e `simular_janela()` repassam esses dois campos.
   - Motivo: a chuva da lavoura confirmada passa a ser a média ponderada das células (#35).
   - Sem geometria, o comportamento é idêntico. `tests/motor/test_balanco.py` e `tests/motor/test_eto.py`, com os casos calculados à mão, não mudaram desde `44ecc47` e passam. Teste novo: `tests/motor/test_geometria.py`. Aviso também na #44.
3. **Outros arquivos compartilhados:**
   - `backend/src/tellus/api/app.py`: routers `umidade`, `vegetacao` e `contrato`, mais o formato único de erro. `_erro` passou a ser `_erro(status, codigo, mensagem, campo=None, origem=None)`, e cada handler informa a origem.
   - `backend/src/tellus/api/umidade.py`: o mesmo formato de erro.
   - `backend/src/tellus/vegetacao/servico.py`: lê o limite por anel do arquivo único (#109).
   - **`pyproject.toml`, `uv.lock` e `package.json` não mudaram.**
4. **Conflitos com a sua 008: já resolvidos por você** em `135e0ac` e `7583eb2`. Conferido na `main` `84f0129`:
   - **`motor/servico.py`:** o `lru_cache` ficou só em `_serie_ponto(lat, lon)` (linha 81). `_serie_com_eto` (linha 72) chama `_serie_ponto` sem geometria e a série por área com geometria, que não é cacheada. Isso evita o `TypeError: unhashable type: 'dict'`.
   - **`app.py`:** o handler `ErroRecomendacao` usa o envelope novo com a origem `"spec 008"` (linha 79).
   - **`DUVIDAS_ETAPA1.md` e `REGISTRO.md`:** os dois lados foram mantidos.
   - Nada a fazer aqui, a não ser conferir se concorda.

## 4. Contrato da 011 e a 008

O que a 011 já expõe (`tellus.contrato`, versão 1.0.0, regra semver em `specs/011-contrato-api/contracts/README.md`):
- **Rotas:**
  - `GET /api/contrato/versao`: versão, `versoes_aceitas` e todos os limites com status;
  - `GET /api/contrato/esquema`;
  - `POST /api/contrato/pedido/validar`: valida e normaliza, sem calcular.
- **Seções da resposta** (`secoes.calcular`):
  - `culturas[].risco_hidrico` (006) e `culturas[].economia` (007), reais;
  - `contextos.{vegetacao,umidade}`, opcionais;
  - `recomendacao`, hoje **pendente**: `secao_recomendacao_pendente()` em `backend/src/tellus/contrato/secoes.py:197`.
- **Erros:** `tipo` erro separado de aviso, com código, mensagem PT-BR e origem. Versão incompatível devolve `versoes_aceitas`. Sem cache, `estado_geral=erro` e `final=false`.
- **Prazo:** `secoes.calcular(..., prazo_s, relogio)` confere os 60 s **só entre as chamadas de módulo**; o erro `tempo_excedido` está em `secoes.py:251`.

**A 008 já existe como rota própria** (`POST /api/recomendacao`, `backend/src/tellus/api/recomendacao.py:34`), **mas ainda não entrou na seção do contrato.** `secoes.calcular` continua usando `secao_recomendacao_pendente()`. **Onde ela entra para fechar a #54:** em `secoes.calcular` (`secoes.py:228`), troque `secao_recomendacao_pendente()` por uma seção montada com a saída da sua recomendação. Siga o mesmo formato das outras seções: `id`, `spec`, `estado`, `versao_modulo`, `conteudo`, `proveniencia[]` com os 6 campos e `cobre`, `avisos` e `erro`. Depois:
- remova o aviso `secao_pendente`;
- deixe `estado_geral=completo` e `final=true` quando tudo estiver ok;
- trate o grupo "não sei" (`secoes.py:310`), que hoje fica indisponível porque compara grupos, papel da 008;
- regenere o exemplo gravado com `python -m tellus.contrato.exemplos`, ou o teste de determinismo falha.

O teste `tests/contrato/test_resposta.py` percorre a resposta e falha se algum número da sua seção não tiver proveniência completa.

**O que a 012 espera:** `frontend/src/lib/comparacao/contrato-provisorio.ts`, na branch `012-interface-web` (pendente de merge), concentra os tipos.
- `ResultadoComparacao.alternativas` ainda não tem equivalente.
- Quando a 008 chegar, a troca é só nesse arquivo: os campos de alternativas e ordenação passam a vir de `secoes.recomendacao.conteudo`.
- O mapeamento campo a campo está em `specs/011-contrato-api/plan.md`, seção "Troca do adaptador da 012".

## 5. Pendências e donos

| Issue | Dono | Bloqueio | Próximo passo |
|---|---|---|---|
| #48, #49, #86–#90, #108, #68 (008 e D-006) | LK | — | **Fechadas** (integradas em `84f0129`). |
| #54 US-011 | a combinar (LK ou Pedro) | — | Trocar a seção pendente do contrato pela saída de `tellus.recomendacao` (seção 4). Agora está desbloqueada. |
| #53 T-025, #95 T-064 | Pedro | — | Desbloqueadas pela 008: provar que incluir ou remover o SMAP não muda a recomendação. Depois fecham #52 (US-010). |
| #56 US-012, #57, #100–#104, #72 | Pedro | #54 | Publicar a branch 012 (em andamento), trocar o adaptador e integrar. #72 (D-010: web responsiva, internet, sem login do produtor) é hipótese no `plan.md` da 012. #104 é o teste de usabilidade com 5 pessoas. |
| #51 T-024, #50 US-009 | — | pós-demo | HLS real exige Earthdata e um leitor de COG; o Pedro decidiu adiar. |
| #33 US-003 | Pedro | — | **Fecha agora** (critérios atendidos), com a limitação registrada no comentário de fechamento. |
| #110 (acompanhamento da 003) | — | — | Issue nova (area:dados-clima, tipo:tarefa): validação INMET fora da A025 (a API do INMET responde 204; o caminho são os ZIPs anuais do portal) e células IMERG vizinhas reais (o caso com várias células só foi verificado com dado sintético). |
| #58, #59, #73, #105–#107 (013) | — | #56 | Depois da 012 funcional. |

**Limitações conhecidas:**
- O prazo de 60 s só é conferido entre módulos. Uma etapa mais longa só é detectada quando termina.
- A demo depende do cache IMERG de Rio Verde. A série versionada em `referencias/clima/rio_verde_go/` (célula −17,75/−50,95) tem 9.039 dias `ok`, de 2001-01-01 a 2025-09-30, e 410 `nao_publicado`. Num clone limpo, sem rede, o cálculo das 3 culturas leva 0,61 s. Qualquer outra célula, como a área de teste do CAR em −17,85/−51,05, ainda exige download com Earthdata (cerca de 20 min).
- Preço (D-005): o sorgo não tem indicador CEPEA e o portal de preços da Conab tem certificado TLS inválido. A margem do sorgo fica indisponível e editável pelo produtor. A cobertura tem receita zero e custo informado pelo produtor.
- O peso das células na chuva por área é a fração em graus, não a área geodésica; o erro entre linhas de latitude é pequeno, mas não foi medido.
- A suíte passou a levar ~60 s por causa dos testes de 10.000 vértices.

## 6. Como rodar e testar

```bash
git pull origin main
cd backend && uv sync && uv run pytest -q        # esperado: 442 passed, 1 skipped
uv run uvicorn tellus.api.app:app --port 8000
cd frontend && npm install && npm run dev        # http://localhost:4321
npm run build
```

Rotas novas para testar à mão:
- `GET /api/contrato/versao`;
- `POST /api/recomendacao` (sua 008);
- `GET /api/vegetacao/contexto?lat=-17.785278&lon=-50.965`;
- `GET /api/umidade/contexto?lat=-17.785&lon=-50.965`;
- `POST /api/lavoura/arquivo` (envie um KML, KMZ, GeoJSON ou .zip);
- `POST /api/clima/serie` com `{geometria, id_geometria}`.

O desenho no mapa fica na tela inicial: aproxime Rio Verde, clique em "Desenhar área" e depois em "Confirmar esta área".

## 7. Retorno pedido

Responda, como comentário na **#48** e numa entrada nova no fim do `REGISTRO.md`:
1. Quais issues você vai pegar agora (a #54 está livre: quem encaixa a 008 no contrato?).
2. Se ficou algum conflito ou teste quebrado depois do seu `git pull` desta nota.
3. Se discorda de alguma decisão da seção 2 ou das mudanças da seção 3, principalmente as do CAR e do motor.
4. Se concorda com a troca do adaptador da 012 por `secoes.recomendacao.conteudo` assim que a #54 entrar.
