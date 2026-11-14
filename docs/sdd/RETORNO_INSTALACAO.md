# Retorno da instalação das ferramentas de IA (14/11/2026)

## Ferramentas

| Ferramenta | Versão | Comando | Status | Evidência curta |
|---|---|---|---|---|
| git | 2.55.0 | `git --version` | ok | — |
| gh | 2.101.0 | `gh auth status` | ok | logado como Pedrojscx, escopos repo e workflow |
| uv | 0.12.17 | `uv --version` | ok | — |
| python | 3.14.7 | `python --version` | ok | — |
| node / npm / npx | 26.8.2 / 12.0.2 / 12.0.2 | `node --version` | ok | — |
| claude | 2.1.325 | `claude --version` | ok | — |
| codex | 0.154.0 | `codex --version` | ok | — |
| Spec Kit (specify-cli) | 1.4.0 (tag v1.4.0, Latest) | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.4.0` | ok | `specify check`: Claude Code e Codex CLI "available"; `specify integration status`: claude e codex instalados, 0 arquivos alterados ou faltando |
| Spec Kit: init Claude | — | `specify init --here --force --integration claude --script sh --non-interactive` | ok | Git não foi recriado; nenhum arquivo rastreado mudou |
| Spec Kit: Codex | — | `specify integration install codex --script sh --integration-options="--skills"` | ok | hash de `.claude/` igual antes e depois; skills founder em `.agents/` intactas |
| graphify (graphifyy) | 0.9.109 | `uv tool install --upgrade graphifyy` | ok | já existia a 0.9.91 |
| graphify: projeto | — | `graphify install --project` e `graphify install --project --platform codex` | ok | `.claude/settings.json`, `CLAUDE.md`, `.codex/hooks.json`, `.codex/skills/graphify`, `AGENTS.md` |
| graphify: exclusões | — | `.graphifyignore` (sintaxe gitignore, lido depois do `.gitignore`) | ok | data/raw/, .venv/, node_modules/, graphify-out/cache/, *.nc4, *.xls, *.xlsx, *.pdf |
| graphify: hook do Git | — | `graphify hook install` | ok | post-commit, post-checkout, post-merge, post-rewrite e merge driver de graph.json |
| context-mode (Claude) | 2.2.0 | `claude plugin marketplace add mksglu/context-mode` e `claude plugin install context-mode@context-mode` | ok | `claude plugin list`: enabled, escopo user |
| context-mode (npm global) | 2.2.0 | `npm i -g --prefix ~/.local context-mode` | ok | `/home/pedrolucas/.local/bin/context-mode` |
| context-mode (Codex) | 2.2.0 | `codex plugin marketplace add mksglu/context-mode`, `codex plugin add context-mode@context-mode`, `context-mode setup --yes --agents codex` | ok | setup: PASS (aviso hook-seen: ainda não visto) |
| ctx-doctor | — | `/context-mode:ctx-doctor` | pendente | exige reiniciar o Claude Code |

## Spec Kit: comandos por agente

| Comando | Claude (`.claude/skills/`) | Codex (`.agents/skills/`) |
|---|---|---|
| constitution, specify, clarify, checklist, plan, tasks, analyze, implement | sim | sim |
| converge (novo na 1.4.0) | sim | sim |
| taskstoissues (extensão `github`) | sim: `speckit-github-taskstoissues` | sim: `$speckit-github-taskstoissues` |

Na 1.4.0, `taskstoissues` saiu do núcleo. Ele vem na extensão oficial **GitHub Integration** (`github`, v1.0.5, autor spec-kit-core, catálogo default). Ela traz o comando `speckit.github.taskstoissues`, que cria issues em ordem de dependência a partir do `tasks.md`. Ela exige `git` e o `github-mcp-server` (ferramentas `list_issues` e `issue_write`). Instalada depois, a pedido (`specify extension add github`). Para registrar no Codex também: `specify integration use codex`, `specify extension add github --force`, `specify integration use claude`. O registro mostra o comando nos dois agentes; `specify integration status`: OK, 0 arquivos alterados. Falta o `github-mcp-server`, sem ele o comando não cria issues.

## Estado do Git

- Remote: `origin` → https://github.com/Pedrojscx/TELLUS.git (público, Issues habilitadas).
- Branch: `main`, igual a `origin/main`.
- Histórico: o merge com `--allow-unrelated-histories` juntou o README do GitHub (`d3582f4`).
- Push: feito. Veja os desvios abaixo.
- `.env`: `git log --all -- .env` vazio, nunca rastreado.
- Meus commits: `8bb6d44` (pesquisa de chuva reprodutível) e `4bb0b9e` (higiene de dados e `.gitignore`).

## Labels criados (19)

area:localizacao, area:dados-clima, area:zarc, area:solo-culturas, area:motor-hidrico, area:economia, area:recomendacao, area:vegetacao, area:umidade-solo, area:api, area:web, area:design, area:infra, tipo:spec, tipo:tarefa, tipo:pesquisa, tipo:bug, agente:claude, agente:codex. Nenhum existia antes.

## Hooks ativos

Os hooks não se sobrescrevem, porque cada um fica num arquivo diferente.

| Onde | Evento | Matcher | Comando |
|---|---|---|---|
| `.claude/settings.json` (projeto) | PreToolUse | `Bash\|Grep` | `graphify hook-guard search` |
| `.claude/settings.json` (projeto) | PreToolUse | `Read\|Glob` | `graphify hook-guard read` |
| `.claude/settings.json` (projeto) | SessionStart | `compact` | `graphify hook-guard compact` |
| plugin context-mode (Claude) | PreToolUse, PostToolUse | Bash, Read, Grep, WebFetch, Write, Edit e outros | `node hook.mjs --agent claude-code` |
| plugin context-mode (Claude) | SessionStart, UserPromptSubmit | todos | `node hook.mjs --agent claude-code` |
| `~/.claude/settings.json` (usuário, já existia) | 13 eventos | `*` | hooks anteriores do usuário |
| `.codex/hooks.json` (projeto) | PreToolUse | `Bash` | `graphify hook-check` (não faz nada; o guia vem do AGENTS.md) |
| `~/.codex/hooks.json` (usuário) | PreToolUse, PostToolUse, SessionStart, UserPromptSubmit | `^(Bash\|apply_patch\|mcp__context_mode__ctx_.*)$` nos dois primeiros | `node .../context-mode/hook.mjs --agent codex`, somado aos hooks que já existiam |

## Pendências que dependem de você

1. Reiniciar o Claude Code e rodar `/context-mode:ctx-doctor`.
2. Abrir o Codex, fazer uma chamada de ferramenta (o aviso "hook-seen" some) e rodar `/ctx-doctor`.
3. Instalar e configurar o `github-mcp-server` no Claude e no Codex. A extensão `github` precisa dele.
4. Opcional: o README do graphify pede `multi_agent = true` em `[features]` no `~/.codex/config.toml` para extração em paralelo. Não mexi.

## Desvios deste prompt

1. **`.gitignore`**: acrescentei `!data/raw/**/`. Sem essa linha o Git não entra nas pastas e não encontra os `FONTE.md` e `*.meta.json`.
2. **Commit e push do passo 7**: não fui eu. Às 20:34 alguém commitou `18965fb "Commit de compartilhamento de arquivos"` com o seu usuário. O commit tinha `.specify/`, as pastas de agente, a config do graphify e `solum-chuva-preview.html`. Depois o mesmo processo rodou `pull --rebase` (às 20:36), desfez o rebase, commitou `babea04` (ignora `.specify/extensions/.cache/` e `graphify-out/`), fez o merge com o README do GitHub (`d3582f4`) e enviou o push. Conferi depois: o `.env` nunca entrou e a ponta do `main` não tem binários de `data/raw`.
3. **Grafo**: o post-commit do graphify rodou no commit `18965fb` e fez um build AST (sem LLM) em `graphify-out/`. Não apaguei. `graphify-out/` agora está no `.gitignore` (por `babea04`).
4. **graphify global**: ao rodar, o graphify atualizou sozinho as skills em `~/.claude/skills/graphify` e `~/.agents/skills/graphify` de 0.9.91 para 0.9.109. Guardou as cópias antigas como `SKILL.md.bak`.
5. **npm global**: `npm i -g context-mode` falhou (EACCES em `/usr/lib/node_modules`). Corrigi com `--prefix ~/.local`, sem sudo e sem mudar a config do npm.
6. **Diff do Codex**: para mostrar o diff antes de editar, rodei os comandos numa cópia com `CODEX_HOME`/`HOME` temporários e só apliquei depois da sua aprovação. Backups de `config.toml` e `hooks.json` ficaram na pasta temporária da sessão.
7. **Histórico público**: `git rm --cached` tira `data/raw` só da ponta. Os `.xls`, `.pdf` e `.json` brutos antigos continuam nos commits anteriores ao `4bb0b9e` (pack de cerca de 10 MiB). Não reescrevi o histórico.
8. **Spec Kit**: `specify init` aceita uma integração por vez. Usei `init` para claude e `specify integration install codex` para o Codex.
