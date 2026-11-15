# Plano de implementação: 012 Interface web

**Branch:** `012-interface-web` · **Spec:** `spec.md` · **Pesquisa:** `research.md`
**Issues:** #56 US-012; #57, #100, #101, #102, #103, #104; decisão #72 (D-010)
**Estado:** planejamento e telas com DADOS DE EXEMPLO. A integração com a API de cálculo está **BLOQUEADA** por #54 (011) e #48 (008).

## Contexto técnico

O frontend existente usa Astro 7, Tailwind 4 e Leaflet, sem framework de UI. Não entra dependência nova
(`package.json` e lockfile intactos). Os scripts de cliente são TypeScript em `<script>` do Astro.
Todo o formato de dados de comparação vive num único adaptador:
`frontend/src/lib/comparacao/contrato-provisorio.ts` ("PROVISÓRIO até a spec 011 (#54)").

## 1. Matriz issue → requisito → dependências → estado

| Issue | Requisito | Depende de | Estado |
|---|---|---|---|
| #57 T-027 localização e confirmação | FR-001; cenário 1 ("área confirmada") | #19 (aberta), #54 | **Parcial preparável**: reaproveita `SeletorLocal` por import. **Bloqueado por #19** nos três modos (desenho e arquivo genérico da 002 não existem no frontend) e pelo gancho de confirmação (R2) |
| #100 T-069 colheita, solo, grupo | FR-002; cenário 1 | #57, #54 | **Preparável agora** (validação local e sessão feitas). **Bloqueado por #54** no formato do pedido e nas faixas de domínio |
| #101 T-070 duas metodologias | FR-003 | #48, #54, #100 | **Preparável agora** (escolha e explicação feitas). **Bloqueado por #48/#54** no envio da metodologia no pedido versionado e no critério de ordem real |
| #102 T-071 premissas editáveis | FR-004 | #42 (005), #46 (007), #54, #100 | **Preparável agora** (padrão × editado, unidade, faixa e origem). **Bloqueado por #42/#46** na lista e nas faixas reais das premissas, e **por #48/#54** no recálculo e no "efeito no resultado" |
| #103 T-072 proveniência, carga, erros | FR-005; edge cases; SC-002 | #54, #57, #100, #101, #102 | **Preparável agora** (bloco de proveniência, erro de fonte e indicador de etapas feitos). **Bloqueado por #54** na lista real de etapas e nos códigos de erro por fonte (#98) |
| #104 T-073 teste de usabilidade | SC-001; Independent Test | #57, #72, #100–#103 | **Bloqueado por #72** e por todas as anteriores. Pode-se só esboçar o roteiro (seção 6) |
| #72 T-041 / D-010 | Assumptions | — | **Decisão pendente.** A proposta do usuário fica como hipótese (seção 3) |
| #56 US-012 | todos | #19, #54 | Não concluível nesta etapa |

## 2. Componentes preparados independentemente da API

Todos estão em `frontend/src/components/comparacao/` e `frontend/src/lib/comparacao/` e leem só a fixture
`frontend/src/fixtures/comparacao/rio-verde-exemplo.json` (`"exemplo": true`).

| Componente | Entradas mínimas (interface local) | Em aberto até a 011 | Risco de retrabalho |
|---|---|---|---|
| `FormEntradas.astro` + `lib/comparacao/validacao.ts` (#100) | `EntradasComparacao` (área, `colheita_soja` AAAA-MM-DD, solo `{textura}` ou `{mm}`, grupo I/II/III/`nao_sei`) | Nomes dos campos no pedido (#96); faixa de datas aceitas; limite de mm; envio por textura ou por classe AD | **Baixo**: as regras seguem as specs 004/005/012; só muda o mapeamento no adaptador |
| `Metodologias.astro` (#101) | `Metodologia` = `cultura_escolhida` / `comparar_alternativas`, mais a cultura | Identificadores da 008/011; critério de ordem real | **Baixo** no texto, **médio** nos identificadores |
| `IndicadorEtapas.astro` + `lib/comparacao/etapas.ts` (#103) | `Etapa{id, rotulo, obrigatoria, estado}`; a regra `podeMostrarComoFinal` é pura | Lista real de etapas e como a API informa o andamento (síncrono, polling ou stream, decisão #71) | **Médio**: a regra "parcial nunca final" fica; a origem dos estados muda |
| `BlocoProveniencia.astro` (#103) | `Proveniencia{fonte, versao, unidade, escala, qualidade, obtido_em, origem_dados, situacao}` | Nomes finais (#97); a API atual usa `procedencia` na 001 e `proveniencia` na 003/010 | **Baixo**: é genérico; o adaptador normaliza |
| `ErroFonte.astro` (#103, SC-002) | `ErroFonte{codigo, mensagem, origem, cache_obtido_em, acao}`, alinhado ao `{"erro": {codigo, mensagem, origem}}` já usado | Campo de ação sugerida e data do cache no contrato (#98) | **Baixo** |
| `CartaoAlternativa.astro` (#56 cenário 2) | `Alternativa{cultura, grupo, decendio, risco_zarc_pct, risco_historico_falta_agua_pct, cenarios[], premissas_usadas, avisos, proveniencia[]}` | Estrutura real da 008 (cenários, percentis D-006, decêndio) | **Médio-alto**: depende do formato do motor |
| `EditorPremissas.astro` + `lib/comparacao/premissas.ts` (#102) | `Premissa{id, nome, tipo, padrao, editado, unidade, minimo, maximo, proveniencia}` | Lista e faixas reais (005/007); como o pedido leva as edições; recálculo | **Médio**: as faixas da fixture são exemplo |
| `ContextoOpcional.astro` (009/010) | `ContextoOpcional{id, titulo, disponivel, resumo, aviso_escala, proveniencia, erro}` | T-068 (#99) na 011 | **Baixo**: o resumo pode vir da resposta real da 010 |
| Reaproveitar `SeletorLocal.astro` (#57) | import sem mudança | Gancho `tellus:area-confirmada` (research R2) | **Baixo** |
| `LayoutComparacao`, `NavComparacao`, `SeloExemplo` | — | O selo sai quando houver dado real | Nenhum |

Verificação local desta etapa:
- `npm run build` passa (8 páginas).
- As regras puras (validação, etapas, premissas) foram conferidas com um script Node de asserções (fora do repositório; casos válidos e inválidos de data, solo, grupo, metodologia, "parcial nunca final" em todos os passos dos 3 cenários e faixa das premissas). O frontend não tem framework de teste: adicionar Vitest seria uma dependência nova, a decidir.
- As telas foram vistas a 360 px e 1280 px.
- Varredura sem "previs*", "produtividade" e "vai chover"; nenhuma chamada `fetch` nas telas novas.

## 3. Pontos que dependem de #72 (D-010) — em aberto

Hipótese operacional registrada (research R1): web responsiva para celular e computador, internet necessária e sem login
obrigatório para o produtor na demonstração.

- O "sem login" vale para o produtor. As fontes 003/009/010 exigem Earthdata **no servidor**. Sem token no servidor, só funcionam os locais com cache ou referência versionada.
- **Em aberto**:
  - nível de acessibilidade exigido (ex.: WCAG);
  - navegadores e versões mínimas;
  - menor largura suportada (as telas foram feitas para 360 px por regra do Maestro, não por decisão da #72);
  - uso offline;
  - termos de uso da credencial Earthdata no servidor;
  - perfil e dispositivo dos participantes do teste #104.

## 4. Contextos 009/010 como seções opcionais

- Ficam numa seção própria, "Contexto da região (opcional)", **depois** do resultado e separada dele. Cada contexto é um `<details>` com selo "contexto opcional" ou "indisponível — não afeta o resultado".
- O indicador de etapas marca "Contextos opcionais" com `obrigatoria: false`: uma falha ou demora ali não impede o resultado final (`etapas.situacao`).
- A 010 já devolve o formato que a seção precisa: produto, versão, célula, período, unidade, qualidade, resolução, `aviso_escala` e indisponível sem substituição. A ligação real espera a T-068 (#99), que define onde o contexto entra na resposta da 011.
- Texto fixo: "Ajuda a interpretar, mas não entra no cálculo. O resultado acima é o mesmo com ou sem estes blocos."

## 5. Ordem sugerida quando as dependências chegarem

1. **#19 + gancho de confirmação** → ligar o `SeletorLocal` ao `FormEntradas` e acrescentar desenho e arquivo da 002 (#57).
2. **#54 (011) publicado** → trocar os tipos de `contrato-provisorio.ts` pelos do contrato e mapear `EntradasComparacao` para o pedido (#100, #101).
3. **#42/#46** → carregar as premissas reais (lista, faixas, fontes) no `EditorPremissas` (#102).
4. **#48 (008)** → chamada real de cálculo, etapas reais no `IndicadorEtapas`, `CartaoAlternativa` com cenários e critério de ordem reais, recálculo com premissas editadas (#101, #102, #103).
5. **#99 (T-068)** → ligar os contextos 009/010 na seção opcional.
6. Tirar o `SeloExemplo` e a fixture das rotas reais (mantê-los só em `/comparacao/exemplo`, se for útil).
7. **#72 decidida** → ajustar acessibilidade e dispositivos e rodar o teste de usabilidade (#104).

## 6. Esboço do roteiro de #104 (não executável ainda)

Caso Rio Verde/GO:
1. Localizar a lavoura e confirmar a área.
2. Informar a colheita da soja, a textura e o grupo "não sei".
3. Escolher "comparar alternativas".
4. Abrir a 1ª alternativa e achar o risco ZARC, o risco histórico, a margem nos 3 cenários, as premissas e as fontes.
5. Editar o preço e comparar com o padrão.
6. Achar um aviso de fonte com cache.

Registrar por participante: conclusão (sim/não), tempo, pedidos de ajuda e qualquer data fora do ZARC tentada. Dispositivos e acesso dependem de #72.

## Como abrir as telas

```
cd frontend && npm install && npm run dev      # http://localhost:4321/comparacao
```

Rotas:
- `/comparacao`
- `/comparacao/entradas`
- `/comparacao/metodologia`
- `/comparacao/carga`
- `/comparacao/resultado`
- `/comparacao/premissas`
- `/comparacao/erros`

A seção "Localizar a lavoura", em `entradas`, só responde com o backend rodando (`cd backend && uv run uvicorn tellus.api.app:app`). As demais telas funcionam sem backend.

## Preço do sorgo como premissa do produtor (D-005), 2026-11-15

- A tela de premissas mostra o preço do sorgo **sem valor padrão**, com o rótulo "Sem cotação oficial (CEPEA não cobre sorgo) — informe a sua". Valor (R$/sc 60 kg), origem informada e data da cotação são obrigatórios. A validação pura está em `lib/comparacao/premissas.ts::validarCotacao` e `validacao.ts::validarDataCotacao`: valor > 0 e dentro da faixa, origem não vazia, data válida e não futura. Os testes estão em `lib/comparacao/cotacao.test.ts`.
- Sem cotação, a margem do sorgo aparece "indisponível", com o motivo, e nunca vira zero (`margensComCotacao`). Com cotação, o resultado mostra "informada pelo produtor", a origem e a data no bloco de proveniência. A margem é recomposta sobre a base de EXEMPLO da fixture (sacas × preço − custo, a fórmula da 007).
- **Backend hoje (main 95753b1)**: a 007 (`economia.margem`, `edicoes.preco_r_saca`) e a 008 (`edicoes_economia[cultura].preco_r_saca`) aceitam só o número. A alteração devolve `origem_novo: "produtor"`, sem origem nem data da cotação. O contrato 1.0.0 (`PremissaEditada`, `extra="forbid"`) também não tem esses campos.
- **Mudança proposta no contrato (MENOR 1.1.0, compatível)**: campos opcionais `origem_informada: str` e `data_informada: date` (não futura) em `pedido.premissas_editadas[]`, devolvidos na resposta em `premissas_editadas[]` e na proveniência `premissas_do_produtor`. Pedidos 1.0.x continuam válidos. O adaptador `contrato-provisorio.ts::premissasParaPedido` já envia os dois campos.
