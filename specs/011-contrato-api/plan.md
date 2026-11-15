# Implementation Plan: Contrato de API

**Branch**: `011-contrato-api` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)
**Base**: `origin/main` f03d966 (006 motor e 007 economia integradas) · **Issues**: #54 (US-011); #55, #96, #97, #98, #99; decisão #71 (D-009)

## Summary

Contrato versionado (semver) entre a interface (012) e o cálculo. O pacote `tellus.contrato` define:

- o **pedido de cálculo** validado: área confirmada (ponto ou geometria), colheita, solo, grupo, metodologia, premissas editadas com o padrão preservado e contextos opcionais;
- a **resposta rastreável** montada em seções:
  - `risco_hidrico`: saída real da 006;
  - `economia`: saída real da 007;
  - `recomendacao`: 008, pendente;
- os **contextos opcionais** 009/010 como blocos opacos;
- a distinção **resultado / aviso / erro por fonte**, com cache e data;
- a regra **"todo número coberto por proveniência completa"**, verificada por um teste que percorre a resposta.

As rotas `/api/contrato/{versao,esquema,pedido/validar}` só validam. Elas não executam a 006, a 007 nem a 008.

## Technical Context

**Language/Version**: Python ≥ 3.12 (uv)
**Primary Dependencies**: FastAPI, pydantic v2 (já presentes; nenhuma dependência nova)
**Storage**: nenhum; a ficha de limites (D-009) fica em `backend/src/tellus/contrato/limites.json`
**Testing**: pytest (`cd backend && uv run pytest -q`)
**Target Platform**: API local (uvicorn)
**Project Type**: web service (backend) + frontend Astro (012, consumidor)
**Performance Goals**: validação do pedido em < 1 s para geometrias dentro do limite de vértices (limite = hipótese D-009)
**Constraints**:
- não alterar as rotas existentes, `app.py`, `pyproject.toml` nem `uv.lock`;
- a 008 não existe;
- os contextos 009/010 estão em branches próprias.
**Scale/Scope**: 1 pacote, 1 router e exemplos gravados

## Constitution Check

| Princípio | Como o plano atende | Situação |
|---|---|---|
| I Rastreabilidade | `Proveniencia` com fonte, versão, período, unidade, localização e qualidade, mais `cobre` (caminhos explicados). O teste `numeros_sem_proveniencia` percorre a resposta | OK |
| II Sem parâmetro inventado | D-009 parametrizável: vértices = valor já em uso no CAR (`hipotese`); arquivo e prazo = `decisao_pendente`, sem valor. A seção 008 fica `pendente`, sem campos inventados | OK |
| III Reprodutibilidade | Hash do pedido normalizado e das seções; teste de determinismo | OK |
| IV Respeito à escala | As seções e os contextos preservam os avisos dos módulos (escala, "não é previsão") | OK |
| V Premissas editáveis | `PremissaEditada` com `valor_padrao` e `valor_novo` | OK |
| VI Motor puro | `tellus.contrato.regras` é puro; a montagem não chama a rede | OK |
| VII Degradação explícita | `EstadoFonte` (ok, cache com data, falha) e `ErroFonte` (código, mensagem PT-BR, origem, cache, ação); `final=False` quando falta seção obrigatória | OK |
| VIII Segredos | Nenhum token no contrato; teste de varredura | OK |
| IX Stack | Python, FastAPI, PT-BR | OK |

Os gates passam, sem violação a justificar.

## Project Structure

```text
specs/011-contrato-api/
├── plan.md, research.md, data-model.md, quickstart.md, decisao-proposta.md, tasks.md
└── contracts/
    ├── README.md                       # versão e regra de compatibilidade
    ├── pedido.schema.json              # gerado do modelo pydantic
    ├── resposta.schema.json
    └── exemplos/*.json                 # válidos e de erro (SC-001)

backend/src/tellus/contrato/
├── __init__.py
├── versao.py      # VERSAO, compatibilidade
├── modelos.py     # pydantic: Pedido, Resposta, Secao, Proveniencia, Aviso, ErroFonte, EstadoFonte, ContextoOpcional
├── regras.py      # puras: geometria (reusa car.regras), cobertura de proveniência, estado geral, hash
├── secoes.py      # adaptadores: 006 real → Secao; 007 real → Secao; 008 pendente; contextos opacos; montar resposta
├── limites.json   # D-009
└── exemplos.py    # gera os exemplos gravados a partir dos módulos reais (offline, Rio Verde)

backend/src/tellus/api/contrato.py      # GET /versao, GET /esquema, POST /pedido/validar
backend/tests/contrato/                 # versão, pedido, resposta, erros por fonte, contextos, determinismo, rota
```

**Structure Decision**: o pacote fica separado dos módulos de cálculo. Ele lê a saída da 006 e da 007 como dados, pelos adaptadores de `secoes.py`, e não altera nenhuma das duas. Quando a 008 chegar, ela entra como mais um adaptador.

## Complexity Tracking

Sem violações.

## Troca do adaptador da 012

O adaptador `012-interface-web:frontend/src/lib/comparacao/contrato-provisorio.ts` concentra os tipos. A troca acontece num ponto só:

| Provisório (012) | Contrato 1.0.0 |
|---|---|
| `EntradasComparacao.area {id_geometria, area_ha, municipio, uf, confirmada}` | `pedido.area` (`tipo: "geometria"`, `geometria`, `id_geometria`, `origem`, `confirmada`) ou `tipo: "ponto"` |
| `colheita_soja` | `pedido.data_colheita_soja` |
| `solo {modo: "textura"\|"mm"}` | `pedido.solo` com `textura` ou `cad_mm` (também `classe` e `granulometria`) |
| `grupo "I"\|"II"\|"III"\|"nao_sei"` | `"GRUPO I"`… ou `"nao_sei"` (mapa fixo no adaptador) |
| `metodologia`, `cultura` | iguais (`cultura` usa as chaves do motor: `milho_2a_safra`…) |
| `Premissa {padrao, editado}` | `pedido.premissas_editadas[] {modulo, id, valor_novo, unidade}`; a resposta devolve `valor_padrao` |
| `ResultadoComparacao.alternativas` | **sem equivalente até a 008**: `secoes.recomendacao.estado = "pendente"`. A tela usa `secoes.risco_hidrico` e `secoes.economia` (cenários conservador/central/favorável reais da 007) |
| `Proveniencia` | `secoes.*.proveniencia[]` (os seis campos e mais `cobre`) |
| `ErroFonte` | `erros[]` (`codigo`, `mensagem`, `origem`, `cache.obtido_em`, `acao`) |
| `ContextoOpcional` | `contextos.{vegetacao,umidade}` (`estado`, `conteudo` opaco, `avisos`, `erro`) |
| `IndicadorEtapas` | `estado_geral` e `final`; `fontes[]` dá o estado por fonte |
