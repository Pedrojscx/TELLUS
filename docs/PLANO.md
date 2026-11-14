# Plano nasa26 — ideia B (segunda safra)
Leia junto com `REGISTRO.md`. Hipóteses técnicas estão marcadas com (H) e podem mudar.

## Escopo essencial
Região: Rio Verde-GO. Entrada: data de colheita da soja, solo (água disponível, editável), premissas de custo, preço e produtividade.
Saída: para milho 2ª safra, sorgo e planta de cobertura — risco de falta de água, produtividade em 3 cenários, margem por hectare, e a fonte e data de cada número.
Fora do escopo essencial: login, hospedagem, imagens de 30 m, previsão do tempo, IA dentro do app.
Também no essencial: janela do ZARC ao lado do nosso risco; tela de fontes com a comparação POWER × estação INMET.
Extras, só depois do fluxo completo: histórico NDVI MODIS do ponto; sequências de 3 safras, só se a regra da cobertura tiver fonte.

## Método (H)
1. Clima: NASA POWER diário desde 1984 para Tmax, Tmin, radiação, umidade e vento. Chuva: fonte plugável, pois o POWER subestima a chuva em Rio Verde (ver REGISTRO). Ordem de preferência: IMERG Final, se houver Earthdata Login; senão POWER corrigido pela estação INMET A025.
2. Água: ETo por FAO-56, Kc por fase da cultura, balanço diário de água no solo, um ano histórico por simulação.
3. Produtividade: FAO-33, perda relativa = Ky × (1 − ETa/ETc). Um resultado por ano histórico; cenários = percentis 25, 50 e 75.
4. Economia: margem = produtividade × preço − custos incluídos. Lista de custos incluídos visível. Tudo editável.
Cada parâmetro (Kc, Ky, duração das fases, custo, preço) fica em `referencias/` com fonte, data e unidade. Sem fonte, o campo recebe `"status": "hipotese"` e a interface mostra isso.

## Arquitetura (H)
- `app/dados/` cliente POWER e MODIS, cache em disco, metadados.
- `app/regras/` balanço hídrico, produtividade, economia. Python puro, sem rede.
- `app/api/` FastAPI. `POST /api/comparar`, `GET /api/fontes`, `GET /api/saude`.
- `web/` HTML e JS sem etapa de build. Bibliotecas copiadas para o repositório, para a demo rodar sem internet.
- `referencias/` YAML com fontes. `data/raw/` respostas originais. `tests/` pytest.
- Ambiente com `uv`. Um comando para iniciar.

## Contrato `POST /api/comparar` (rascunho, validar antes de distribuir)
Pedido: `{lat, lon, data_colheita_soja, agua_disponivel_mm, premissas?: {cultura: {preco, custo, produtividade_potencial}}}`
Resposta: `{meta: {fontes[], obtido_em, periodo, avisos[]}, alternativas: [{cultura, data_plantio, risco: {anos_simulados, prob_perda_maior_30pct, deficit_mediano_mm}, cenarios: {conservador, central, favoravel: {produtividade, receita, custo, margem}}, premissas_usadas, explicacao}]}`
Erros: `{erro: {codigo, mensagem, origem}}`. Fonte fora do ar com cache: responde com `avisos` e a data do cache.

## Agentes, por etapa
| Papel | Ferramenta | Arquivos | Depende de | Aceite |
|---|---|---|---|---|
| Coordenação e integração | Claude Code (Maestro) | `docs/`, `REGISTRO.md`, merges | — | Contrato validado; `main` sempre roda |
| Dados NASA | Codex | `app/dados/`, `tests/dados/` | contrato | POWER real com cache, -999 tratado, teste sem rede passa |
| Regras e economia | Claude Code | `app/regras/`, `referencias/`, `tests/regras/` | contrato | Cálculo reproduz um caso feito à mão; toda constante tem fonte ou marca de hipótese |
| Backend | Codex | `app/api/`, `tests/api/` | dados e regras | Contrato cumprido; erros legíveis |
| Interface | Codex | `web/` | contrato (pode usar resposta de exemplo) | Fluxo completo no navegador; estados de carga e erro |
| Revisão e testes | ferramenta oposta à do autor | só relato e `tests/` | entrega do autor | Relato de falhas com passos para repetir |
Etapa 1: Dados NASA + Regras em paralelo (2 agentes). Etapa 2: Backend + Interface. Etapa 3: Revisão. Cada um em seu andar ou worktree e branch `feat/<papel>`. Só o Maestro faz merge.
Devolutiva de todo agente: commit, arquivos, testes rodados e resultado, limitações.

## Cronograma reverso (BRT)
| Até | Entrega |
|---|---|
| sáb 03h | Contrato fechado, esqueleto, delegação de teste no Maestri, fontes Conab e ZARC achadas |
| sáb 12h | Fluxo completo com dados reais: POWER → balanço → margem → tela |
| sáb 20h | Premissas editáveis, fontes na tela, estados de erro, NDVI MODIS |
| sáb 24h | Revisão cruzada e teste no navegador registrados |
| dom 08h | Correções. Nada novo depois deste ponto |
| dom 11h | Demo ensaiada, README, material de submissão |
| dom 12h | Prazo |

## Verificações de qualidade
- [ ] Cada número na tela mostra fonte e data.
- [ ] Mesmo pedido, mesma resposta (teste automático).
- [ ] Caso feito à mão confere com o código.
- [ ] Premissas editáveis mudam o resultado.
- [ ] POWER fora do ar: o app usa o cache e avisa.
- [ ] Valores -999 não entram em cálculo.
- [ ] Instalação do zero com um comando, testada.
- [ ] Fluxo principal testado no navegador, com resultado anotado no registro.
