Você está no repositório local /home/pedrolucas/tellus (projeto Tellus). Objetivo desta sessão: instalar e verificar as ferramentas de IA do projeto e preparar Git e GitHub. Não crie código de aplicação e não instale Astro, Tailwind ou dependências do backend; isso sairá das specs.

Contexto: leia REGISTRO.md. O docs/PLANO.md é histórico; a arquitetura dele será substituída pelas specs.

Regras
- Nunca leia, imprima ou commite o conteúdo de .env (contém EARTHDATA_TOKEN).
- Antes de qualquer push, reescrita de histórico ou comando destrutivo, mostre o comando e peça minha confirmação. Nunca use --force.
- Antes de instalar cada ferramenta, confira na documentação oficial o comando e a versão atuais, sem confiar em memória.
- Se um passo falhar, tente uma correção razoável uma vez; se falhar de novo, registre e siga.

1. Pré-requisitos
Registre as versões de git, gh, uv, python, node, npm, npx e claude. Rode `gh auth status`; se não estiver autenticado, pare e me peça para rodar `gh auth login`.

2. Repositório
a. `git status`: liste o que está fora de commit (a pesquisa de chuva em scripts/, docs/pesquisa_chuva/ e data/processed/ provavelmente está).
b. .gitignore: manter .venv/, __pycache__/, node_modules/, .env; acrescentar .env.* com exceção de .env.example, data/raw/** com exceções !data/raw/**/FONTE.md e !data/raw/**/*.meta.json, graphify-out/cache/, .astro/, dist/.
c. `git rm -r --cached data/raw` mantendo os arquivos no disco; readicione só FONTE.md e *.meta.json. Confirme com `git log --all -- .env` que o .env nunca foi rastreado; se foi, pare e me avise.
d. Commits separados, mensagens em PT-BR: (1) pesquisa de chuva reprodutível; (2) higiene de dados e .gitignore.
e. Remote: `git remote add origin https://github.com/Pedrojscx/TELLUS.git` e `git fetch origin`. Se origin/main estiver vazio, prepare o push. Se tiver commits, mostre `git log origin/main --oneline` e a lista de arquivos, proponha a estratégia de integração (rebase ou merge com --allow-unrelated-histories) e espere minha decisão.
f. `gh repo view Pedrojscx/TELLUS --json hasIssuesEnabled,visibility`: confirme que as Issues estão habilitadas.
g. Crie os labels com gh label create, pulando os que já existirem: area:localizacao, area:dados-clima, area:zarc, area:solo-culturas, area:motor-hidrico, area:economia, area:recomendacao, area:vegetacao, area:umidade-solo, area:api, area:web, area:design, area:infra, tipo:spec, tipo:tarefa, tipo:pesquisa, tipo:bug, agente:claude, agente:codex.

3. Spec Kit (github/spec-kit)
a. Descubra a última tag estável com `gh release list -R github/spec-kit -L 1` e instale com `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@<tag>`. Rode `specify version` e `specify check`.
b. Leia `specify init --help`. Inicialize no diretório atual sem recriar o Git e sem apagar arquivos, para Claude Code e para Codex, com scripts sh. Se a versão aceitar várias integrações num init, use isso; senão, rode o init para claude e depois para codex com a opção de mesclar em diretório existente, e confira que o segundo não sobrescreveu o primeiro.
c. Confirme que .specify/ existe e que os comandos ou skills speckit (constitution, specify, clarify, checklist, plan, tasks, analyze, implement, taskstoissues) estão presentes para os dois agentes. Não execute nenhum comando /speckit nesta sessão.
d. Verifique se existe extensão oficial de GitHub Issues no catálogo do Spec Kit. Só registre o que ela faz; não instale.

4. Graphify (pacote PyPI graphifyy, CLI graphify)
a. `uv tool install graphifyy` e confira a versão.
b. `graphify install --project` para Claude Code e a variante para Codex (confira o parâmetro de plataforma na ajuda).
c. Configure exclusões de data/raw/, .venv/, node_modules/, graphify-out/cache/ e binários (.nc4, .xls, .pdf) pelo mecanismo documentado do graphify.
d. Se existir, `graphify hook install` para atualizar o grafo nos commits. Não construa o grafo agora.

5. Context-mode (mksglu/context-mode)
a. Tente pelo CLI: `claude plugin marketplace add mksglu/context-mode` e `claude plugin install context-mode@context-mode` (confira em `claude plugin --help`). Se o CLI não suportar, me entregue os dois comandos /plugin exatos para eu digitar.
b. Codex: siga o README oficial (instalação global e entrada em ~/.codex/config.toml). Mostre o diff antes de editar o arquivo.
c. O doctor (/context-mode:ctx-doctor) exige reinício; registre como pendência minha.

6. Coexistência de hooks
Graphify e context-mode instalam hooks PreToolUse. Leia o .claude/settings.json final, confirme que nenhum sobrescreveu o outro e liste os hooks ativos.

7. Commit e push
Commite .specify/, as pastas de agente criadas, a configuração do graphify e o .gitignore. Peça confirmação e faça push para origin main.

8. Retorno
Crie docs/sdd/RETORNO_INSTALACAO.md com: tabela ferramenta | versão | comando | status (ok, falhou, pendente) | evidência curta; estado do Git (remote, branch, último commit, se houve push); labels criados; hooks ativos; pendências que dependem de mim; todo desvio deste prompt com o motivo. Commite e envie. Termine com: "Retorno salvo em docs/sdd/RETORNO_INSTALACAO.md. Volte à conversa de planejamento."
