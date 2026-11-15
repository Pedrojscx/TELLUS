# Data Model: 011 Contrato de API (versão 1.0.0)

## Pedido de cálculo (`PedidoCalculo`)

| Campo | Tipo | Regra |
|---|---|---|
| `versao_contrato` | str semver | obrigatório; MAIOR igual e MENOR ≤ ao do servidor, senão `versao_incompativel` |
| `area` | `AreaPonto` \| `AreaGeometria` | `confirmada` precisa ser `true` (spec 012/#57: nenhum cálculo sem área confirmada) |
| `area.tipo="ponto"` | `lat`, `lon` | faixa geográfica |
| `area.tipo="geometria"` | `geometria` GeoJSON Polygon/MultiPolygon, `id_geometria`, `origem` (car, upload_sicar, desenho, arquivo) | validada por `car.regras.validar_poligono` com o limite D-009; inválida → `geometria_invalida`, o cálculo não inicia |
| `data_colheita_soja` | date AAAA-MM-DD | data real |
| `solo` | exatamente um entre `textura` (arenosa, media, argilosa), `cad_mm` (> 0), `classe` (classe AD do ZARC) e `granulometria` (areia+silte+argila = 100) | vocabulário da spec 005 |
| `grupo` | `GRUPO I` \| `GRUPO II` \| `GRUPO III` \| `nao_sei` | `nao_sei` = todos os grupos separados (spec 004) |
| `metodologia` | `cultura_escolhida` \| `comparar_alternativas` | spec 008 FR-001 |
| `cultura` | `milho_2a_safra` \| `sorgo_granifero_2a_safra` \| `braquiaria_cobertura` | obrigatória só em `cultura_escolhida` |
| `premissas_editadas` | lista de `PremissaEditada` | ids únicos |
| `contextos` | `{vegetacao: bool, umidade: bool}` | padrão `false` |

`PremissaEditada`: `modulo` (`motor`, `economia` ou `culturas`), `id` (chave aceita pelo módulo, ex. `preco_r_saca`, `custo_item.8`), `valor_novo` (number), `unidade`, `valor_padrao` (number ou null; a resposta o preenche).

## Resposta de cálculo (`RespostaCalculo`)

| Campo | Conteúdo |
|---|---|
| `versao_contrato` | versão do servidor |
| `pedido` | pedido normalizado + `hash_pedido` |
| `estado_geral` | `final` \| `final_com_cache` \| `incompleto` \| `erro` |
| `final` | bool; `true` só em `final*` |
| `secoes` | `{risco_hidrico, economia, recomendacao}`: cada uma é uma `Secao` |
| `contextos` | `{vegetacao, umidade}`: cada um é um `ContextoOpcional` |
| `fontes` | lista de `EstadoFonte` |
| `avisos` | lista de `Aviso` (`tipo="aviso"`) |
| `erros` | lista de `ErroFonte` (`tipo="erro"`) |
| `hipoteses` | lista de textos (o que é hipótese no resultado) |
| `versoes` | `{contrato, hash_pedido, hash_principal, secoes: {id: versao_modulo}}` |

`Secao`: `id`, `spec`, `obrigatoria`, `estado` (`disponivel`, `indisponivel`, `pendente` ou `erro`), `versao_modulo`, `conteudo` (dict ou null), `proveniencia` (lista), `avisos`, `erro`.

`Proveniencia`: `id`, `fonte`, `versao`, `periodo`, `unidade`, `localizacao`, `qualidade` (todos str não vazios), `url`, `obtido_em`, `situacao` (`fonte`, `cache`, `hipotese`, `editado` ou `calculado`), `cobre` (padrões de caminho relativos ao `conteudo`, `*` = qualquer chave ou índice).

`EstadoFonte`: `fonte`, `estado` (`ok`, `cache` ou `falha`), `obtido_em`, `erro`.

`ErroFonte`: `tipo="erro"`, `codigo`, `mensagem` (PT-BR), `origem`, `campo`, `cache` (`{disponivel, obtido_em}`), `acao`.

`ContextoOpcional`: `id`, `spec`, `estado` (`disponivel`, `indisponivel`, `erro` ou `nao_solicitado`), `conteudo` (opaco), `avisos`, `erro`.

## Estados e transições

- Seção obrigatória `pendente` ou `indisponivel` → `estado_geral = incompleto`, `final = false`.
- Fonte obrigatória em `falha` sem cache → seção `erro` → `estado_geral = erro`, `final = false`. Nenhum número parcial é tratado como final.
- Fonte em `cache` → `final_com_cache`, com aviso `cache_usado` e data.
- Contextos nunca mudam `estado_geral`, `final` nem `hash_principal`.

## Erro de API (envelope unificado proposto)

`{"erro": {"codigo", "mensagem", "origem", "campo", "versoes_aceitas"?}}`
