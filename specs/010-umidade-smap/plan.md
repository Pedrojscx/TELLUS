# Plano de implementação: 010 Umidade SMAP

**Branch:** `010-umidade-smap` · **Spec:** `spec.md` · **Issues:** #52 (história), #53, #93, #94, #95, #70 (decisão)

## Contexto técnico

Python ≥ 3.12, uv, FastAPI, h5py e httpx (já são dependências). Pacote `tellus.umidade`, no
mesmo modelo de `tellus.clima`. Não entra dependência nova.

## Estrutura

| Arquivo | Papel | Issues |
|---|---|---|
| `backend/src/tellus/umidade/regras.py` | Puro: contrato de contexto regional (`item_contexto`, `validar_item`, termos e chaves proibidos), grade EASE-Grid 2.0 parametrizável, células da geometria, flag de qualidade | #53, #93, #94 |
| `backend/src/tellus/umidade/cliente.py` | CMR público, recorte OPeNDAP DAP4 com `EARTHDATA_TOKEN` do ambiente, extração HDF5 com conferência de índice, cache CSV por célula + `.meta.json` | #93 |
| `backend/src/tellus/umidade/servico.py` | Monta a resposta, aplica a hipótese de produto e janela (#70), degradação explícita e a guarda `_garantir_contrato` | #53, #93, #94, #95 |
| `backend/src/tellus/api/umidade.py` | `GET /api/umidade/produtos`, `GET /api/umidade/contexto?lat&lon[&produto&variante&data&inicio&fim]`, `POST /api/umidade/contexto {geometria,...}` | — |
| `referencias/umidade/` | Ficha dos candidatos (`produtos.json`), `FONTE.md`, evidência do CMR | #70 |
| `scripts/preparar_umidade.py` | Bruto CMR + recorte real (com token) + exportação da referência | #70 |

## Contrato de resposta (para a spec 012)

`natureza`, `opcional`, `uso`, `local`, `produto{situacao: hipotese}`, `variante`,
`regra_periodo{janela_dias, inicio, fim, contagem, situacao: hipotese}`, `decisoes_pendentes[D-008]`,
`celulas[]`, `itens[]`, `avisos[]`, `origem_dados`, `dado_sintetico`, `obtido_em`.

Cada item traz `estado` (disponível/indisponível), `valor`, `motivo`, `produto`,
`versao{valor, situacao}`, `celula{grade, linha, coluna, centro, tamanho_km, distancia_km}`,
`periodo{inicio, fim, data, variante, granulo}`, `unidade{valor, situacao}`,
`qualidade{flag, recomendada, texto}`, `resolucao` e `aviso_escala{espacial, temporal}`.

Erros vêm como `{"erro": {"codigo", "mensagem", "origem"}}`: `sem_cache` (404), `fonte_indisponivel` (503),
`produto_desconhecido`, `variante_desconhecida`, `periodo_invalido`, `geometria_invalida` e `coordenada_invalida` (422).

## Checagem da constituição

- Rastreabilidade e sem parâmetro inventado: a grade, as variáveis, o fill e a flag vêm do CMR e do guia NSIDC. O produto e a janela são `hipotese`.
- Reprodutibilidade: a janela termina no último dia do cache, não no relógio (teste de determinismo).
- Respeito à escala: o aviso espacial e temporal acompanha todo item (SC-001).
- Degradação explícita: com cache, aviso `cache_usado` com a data; sem cache, erro que nomeia "NASA SMAP … (NSIDC DAAC)".
- Segredos: o token só vem do ambiente e não é gravado no meta (teste).

## Fora do escopo

Tela (spec 012), registro do router no `app.py` (feito pelo Maestro) e o teste comparativo
com o motor de recomendação (spec 008, ainda inexistente).
