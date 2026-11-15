Você está no repositório /home/pedrolucas/tellus (TELLUS). Situação: houve dois trabalhos de SDD em paralelo. O do LK está na `main` e no GitHub (constituição v1.0.0 com 7 princípios, `docs/sdd/MAPA_SPECS.md`, specs 001 a 007 em branches `NNN-nome`, spec 001 já implementada). O do Pedro está só no disco, sem commit, na branch `sdd/etapa-1` (constituição com 9 princípios, `docs/sdd/MAPA_FEATURES.md`, 13 specs em `specs/`, `docs/sdd/DUVIDAS_ETAPA1.md`, `docs/sdd/BASE_REFERENCIA_SOLO_CULTURAS.md`). Decisão: o trabalho do LK é a fonte oficial. O do Pedro vira insumo de revisão, sem substituir nada.

Regras
- Nunca leia ou exiba .env.
- Não edite arquivos que vieram da `main` do LK (constituição, MAPA_SPECS, specs dele, código). Só crie os arquivos de saída pedidos aqui.
- Antes de qualquer commit, push, troca de branch com alterações pendentes ou comando destrutivo, mostre o comando e espere minha confirmação. Commits sem linha Co-Authored-By de IA e sem rodapé de ferramenta (padrão combinado com o LK).
- Não abra issues, não rode plan, tasks nem implement.

1. Preservar o trabalho do Pedro
a. `git status` e `git log -3` em `sdd/etapa-1`. Liste os arquivos novos e modificados.
b. Proponha um commit único em `sdd/etapa-1` ("SDD etapa 1 do Pedro: rascunho paralelo, referência para conciliação") e o push dessa branch como `sdd/etapa-1-pedro`, para o LK poder consultar. Espere minha confirmação. Ela nunca será mesclada na main.

2. Atualizar com a main
`git switch main`, `git pull origin main`. Confirme que existem `.specify/memory/constitution.md` (versão do LK), `docs/sdd/MAPA_SPECS.md`, o fim do `REGISTRO.md`, `docs/sdd/SINCRONIA_PEDRO.md` (se estiver só no disco, mantenha) e as branches remotas `NNN-*` (`git branch -r`). Liste as issues abertas com `gh issue list -R Pedrojscx/TELLUS --limit 50` e quem está em cada uma.

3. Conciliação
Leia as duas constituições, os dois mapas e as specs equivalentes (do Pedro via `git show sdd/etapa-1:<caminho>`; do LK nas branches `NNN-*`). Crie `docs/sdd/CONCILIACAO_PEDRO.md` com:
- Tabela de equivalência: spec do Pedro | spec do LK | cobre? (sim, parcial, não) | o que só existe no do Pedro.
- Princípios do Pedro sem equivalente na constituição do LK (verifique em especial: respeito à escala com aviso de resolução; degradação explícita com cache e erro legível; premissas editáveis mostrando valor padrão e valor do produtor; rastreabilidade com versão do produto e informação de qualidade). Para cada um, uma proposta de emenda curta no formato de governança da constituição do LK, sem aplicar.
- Dúvidas D-001 a D-011 do Pedro: para cada uma, se a spec do LK já decidiu (cite a decisão e o arquivo), se continua aberta ou se não se aplica.
- Hipóteses do LK que mais mudam o resultado (perda severa de 30%, solo na capacidade de campo, semeadura 3 dias após a colheita, ordenação por margem no cenário conservador, braquiária solteira usando o ZARC de milho com braquiária) com a fonte que falta a cada uma.
- A pesquisa do WFS do CAR (spec 001 do Pedro): diga se o mapa do LK a cobre; se não, proponha como spec extra.

4. Preparar as specs atribuídas ao Pedro
Na divisão do LK, o Pedro fica com 003 zarc e 004 solo-culturas. Para cada uma: nome da branch, se a spec já existe, issue correspondente e se alguém já a pegou, dependências e o que a spec do Pedro acrescenta a ela. Não troque de branch para editar.

5. Retorno
Crie `docs/sdd/RETORNO_CONCILIACAO.md` (sem commit) com: comandos usados, o que foi commitado e enviado (com hashes) ou não, estado da main e das branches, resumo da conciliação em até 15 linhas, situação das specs 003 e 004 e bloqueios. Termine com: "Retorno salvo em docs/sdd/RETORNO_CONCILIACAO.md. Volte à conversa de planejamento."
