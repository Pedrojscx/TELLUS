# Retorno da instalação: máquina do LK (Windows)

Data: 2026-11-14. Máquina: Windows 11 Pro, Git Bash. Conta GitHub: `asasdepapelmache` (permissão WRITE em Pedrojscx/TELLUS).

O Pedro já tinha commitado a parte do repositório: .gitignore, `data/raw` fora do Git, spec-kit 1.4.0 (claude + codex), skills do graphify, hooks e labels. Nesta máquina só instalei o que é local, e não refiz nada do que já estava no repo.

## Ferramentas

| Ferramenta | Versão | Comando | Status | Evidência |
|---|---|---|---|---|
| git | 2.56.0.windows.4 | já existia | ok | `git --version` |
| gh | 2.101.0 | já existia | ok | `gh auth status`: logado como asasdepapelmache, escopo `repo` |
| python | 3.14.7 | já existia | ok | `python --version` |
| node / npm / npx | 24.20.0 / 11.19.0 / 11.19.0 | já existia | ok | `--version` |
| claude | 2.1.296 | já existia | ok | `claude --version` |
| uv | 0.13.8 | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` (docs.astral.sh) | ok | `uv --version` |
| specify-cli | 1.4.0 | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.4.0` | ok | `specify version` mostra 1.4.0; `specify check`: "Specify CLI is ready to use!" |
| graphify (graphifyy) | 0.9.109 | `uv tool install graphifyy` | ok | `graphify --version`; o skill do projeto já estava na 0.9.109 (`.graphify_version`) |
| graphify git hooks | 0.9.109 | `graphify hook install` | ok | post-commit, post-checkout, post-merge e post-rewrite instalados; merge driver registrado |
| graphify skill global | 0.9.109 | `graphify install --platform claude` | ok | atualizado de 0.9.92 em `~/.claude/skills/graphify` |
| context-mode (Claude Code) | 2.2.0 | `claude plugin marketplace add mksglu/context-mode` e depois `claude plugin install context-mode@context-mode` | ok | `claude plugin list`: enabled, escopo usuário |
| context-mode doctor | n/a | `/context-mode:ctx-doctor` | pendente | precisa reiniciar o Claude Code |
| codex + context-mode no Codex | n/a | n/a | não se aplica | não uso Codex; só o Pedro usa |

## Spec Kit

- `.specify/integration.json` registra as integrações `claude` e `codex`, scripts `sh`, versão 1.4.0 (commitado pelo Pedro).
- Skills presentes em `.claude/skills/` e em `.agents/skills/`: constitution, specify, clarify, checklist, plan, tasks, analyze, implement e converge.
- `taskstoissues` não aparece: na 1.4.0 ele saiu do núcleo. Hoje fica na extensão oficial **GitHub Integration** (`github`, v1.0.5, catálogo default, autor spec-kit-core), descrita como "create GitHub issues from a feature's task list". Instalação: `specify extension add github`. Não instalei.
- No catálogo community há outras extensões de issues (Sanduq, de samykabu), mas são só para consulta e não dá para instalar direto.
- Não rodei nenhum comando `/speckit`.

## Estado do Git

- Remote: `origin` aponta para https://github.com/Pedrojscx/TELLUS.git
- Branch: `main`, avancei por fast-forward até `d3582f4` (push do Pedro), sem merge nem rebase.
- `.env` criado localmente com `EARTHDATA_TOKEN`. Está ignorado (`.gitignore:7`) e `git log --all -- .env` mostra que ele nunca foi rastreado.
- Push: só deste arquivo de retorno.

## Labels

Já existiam todos os 19, criados pelo Pedro: area:localizacao, area:dados-clima, area:zarc, area:solo-culturas, area:motor-hidrico, area:economia, area:recomendacao, area:vegetacao, area:umidade-solo, area:api, area:web, area:design, area:infra, tipo:spec, tipo:tarefa, tipo:pesquisa, tipo:bug, agente:claude, agente:codex. Não criei nenhum. Issues estão habilitadas e o repo é público.

## Hooks ativos (Claude Code)

No projeto (`.claude/settings.json`, graphify):
- PreToolUse `Bash|Grep`: `graphify hook-guard search`
- PreToolUse `Read|Glob`: `graphify hook-guard read`
- SessionStart `compact`: `graphify hook-guard compact`

No plugin context-mode (escopo usuário, `hooks/claude-code.json`):
- PreToolUse e PostToolUse: Bash, PowerShell, Read, Grep, WebFetch, Write, Edit, NotebookEdit e as ferramentas `ctx_*`
- SessionStart e UserPromptSubmit: todos

Ficam em arquivos diferentes e o Claude Code executa os dois conjuntos, então nenhum sobrescreveu o outro. O `.claude/settings.json` do projeto não foi alterado.

Git hooks locais (graphify): post-commit, post-checkout, post-merge, post-rewrite.

## Pendências do LK

1. Reiniciar o Claude Code e rodar `/context-mode:ctx-doctor`.
2. Decidir se instalo a extensão `github` do Spec Kit quando chegar a hora de transformar tasks em issues.

## Desvios do prompt original

- **Repositório (passos 2a a 2g):** o Pedro já tinha feito tudo. Só fiz fetch e fast-forward e conferi o resultado.
- **Spec Kit init (3b):** não rodei, porque `.specify/` e as skills já estão commitados. Instalei só o CLI, na mesma tag v1.4.0.
- **`graphify install --project` (4b) e exclusões (4c):** já estão no repo (skills 0.9.109 e `.graphifyignore`), então não reinstalei.
- **Codex (5b):** pulado, porque não uso Codex nesta máquina.
- **taskstoissues (3c):** não existe na 1.4.0; ver a seção Spec Kit.
- **Nome do arquivo:** usei `RETORNO_INSTALACAO_LK.md` em vez de `RETORNO_INSTALACAO.md` para não conflitar com um eventual retorno do Pedro.
- **uv:** não estava instalado, então instalei pelo instalador oficial do Windows.
