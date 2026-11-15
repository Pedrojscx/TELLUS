# Tellus Constitution

## Core Principles

### I. Rastreabilidade

Todo número exibido ao produtor ou devolvido pelo contrato de API MUST trazer: fonte, versão do
produto, período coberto, unidade, localização (ponto, célula, município ou praça) e informação
de qualidade (dias válidos, cobertura, bandeira ou aviso).

Regra verificável: para cada campo numérico da resposta existe um registro de proveniência com
os seis itens acima preenchidos; um teste automático percorre a resposta e falha se algum número
não tiver o registro completo.

Motivo: o produtor e o revisor precisam saber de onde veio cada número antes de confiar nele.

### II. Sem parâmetro inventado

Nenhum parâmetro agronômico ou econômico entra no produto sem fonte. Valor sem fonte MUST ter
status `hipotese`, visível na interface e presente no contrato de API.

Regra verificável: todo parâmetro da base de referência tem os campos fonte, data, unidade e
validade regional, ou então status `hipotese`; um teste falha se houver parâmetro sem fonte e sem
esse status; a interface mostra a marca de hipótese ao lado de cada valor nessa condição.

Motivo: um número sem origem, mostrado como fato, engana o produtor.

### III. Reprodutibilidade

O mesmo pedido com o mesmo cache MUST gerar a mesma resposta. Dados brutos MUST ser recriados
por scripts e MUST NOT ser versionados no Git.

Regra verificável: um teste automático faz o mesmo pedido duas vezes sobre o mesmo cache e
compara as respostas, que devem ser iguais; `git ls-files` não lista arquivos brutos de dados
(só os registros de fonte e metadados); cada conjunto bruto tem um script que o recria e um
registro com consulta, data de obtenção e hash.

Motivo: sem repetição não há como conferir nem corrigir um resultado.

### IV. Respeito à escala

A resolução e a limitação de cada produto de dados MUST aparecer junto do resultado que o usa.
Frequência histórica MUST NOT ser apresentada como previsão.

Regra verificável: cada resultado mostra a resolução espacial e temporal da fonte e o seu limite
de uso; nenhum texto da interface ou do contrato usa "previsão", "vai chover" ou equivalente para
número derivado de série histórica; produtos de escala regional trazem aviso explícito de escala.

Motivo: uma célula de quilômetros não é a lavoura, e o passado não é a próxima safra.

### V. Premissas editáveis

O produtor MUST poder substituir qualquer premissa econômica ou agronômica e ver o efeito no
resultado.

Regra verificável: toda premissa usada no cálculo aparece em uma lista editável; ao trocar um
valor, o resultado é recalculado e mostra o valor padrão, o valor do produtor e a origem de cada
um; um teste troca uma premissa e confere o efeito esperado, inclusive quando o efeito é nulo.
Editar uma premissa não autoriza plantio fora do ZARC. Valores incompatíveis com a fonte
ou com o domínio físico devem gerar erro claro, sem ajuste silencioso.

Motivo: a realidade da fazenda vale mais que a média da região.

### VI. Motor de cálculo puro

O motor de cálculo MUST ser puro: sem acesso à rede, sem leitura de relógio e sem estado oculto.
Ele MUST ser testado contra pelo menos um caso calculado à mão.

Regra verificável: os testes do motor rodam com a rede bloqueada; existe ao menos um caso com as
contas feitas à mão, documentadas passo a passo, e o teste compara o resultado do motor com esse
caso dentro de uma tolerância declarada.

Motivo: só um cálculo isolado pode ser conferido linha a linha.

### VII. Degradação explícita

Quando uma fonte estiver indisponível, o sistema MUST usar o cache e avisar com a data do cache.
Sem cache, MUST devolver erro legível que nomeia a origem.

Regra verificável: um teste simula a queda de cada fonte externa; com cache, a resposta traz um
aviso com a fonte e a data do cache; sem cache, a resposta traz erro com código, mensagem em
português e nome da fonte; nenhum caso devolve resultado silenciosamente incompleto.

Motivo: um resultado que esconde uma falha é pior que um erro claro.

### VIII. Segredos fora do Git

Segredos MUST ficar fora do Git. Credenciais Earthdata MUST entrar só por variável de ambiente.

Regra verificável: `.env` está no `.gitignore` e `git log --all -- .env` é vazio; uma checagem
automática de segredos roda antes de cada integração; nenhum arquivo versionado, log ou resposta
da API contém token; agentes de IA não leem nem exibem `.env`.

Motivo: uma credencial publicada não volta a ser secreta.

### IX. Stack, idioma e forma de trabalho

O projeto MUST seguir as restrições da seção "Restrições de Stack e Idioma" e o fluxo da seção
"Fluxo de Trabalho e Portões de Qualidade".

Regra verificável: cada item dessas duas seções tem um critério que a revisão confere antes da
integração.

Motivo: dois agentes de IA e uma equipe humana só trabalham juntos com regras comuns.

## Decisões de Dados e Escopo

Acrescentado na versão 1.1.0, ao integrar o trabalho paralelo de 14/11. As decisões já constavam
nas specs; aqui passam a valer para todo o projeto.

- Chuva: IMERG Final é a fonte principal e a estação INMET mais próxima é a referência local. A
  chuva do NASA POWER MUST NOT entrar no balanço hídrico, nem crua nem corrigida (pesquisa de
  14/11: viés de -27% em jan–jun e de -56% em 2025 contra a estação A025). O POWER segue como
  fonte de temperatura, radiação, umidade e vento.
- Cobertura nacional: onde faltar dado oficial do local (praça Conab, janela ZARC, estação INMET
  próxima), o sistema MUST usar a referência mais próxima e informar qual é e a que distância, ou
  declarar a lacuna. Nunca preenche em silêncio. Rio Verde-GO é o caso de validação e da demo.
- Escopo até o prazo (2026-11-15, 12h BRT; congelamento às 08h): o fluxo funcional vem antes dos
  extras (vegetação, SMAP, identidade visual). Um extra só entra em `main` depois do fluxo
  completo funcionando.

## Restrições de Stack e Idioma

- Frontend: Astro com Tailwind.
- Backend: Python gerenciado com uv.
- Comunicação entre frontend e backend: só por contrato de API versionado. Mudança incompatível
  no contrato exige nova versão.
- Implementação: Claude Code e Codex.
- Idioma: specs, documentos, commits e textos da interface em PT-BR. As specs mantêm os nomes de
  seção dos templates do Spec Kit.
- Specs descrevem o quê e o porquê. Specs MUST NOT citar framework, biblioteca ou detalhe de
  implementação; isso fica no plano.
- Identidade visual: paleta e identidade visual ainda não existem. São uma feature própria,
  posterior ao fluxo funcional. Até lá, a interface usa estilo neutro e não fixa marca.

## Fluxo de Trabalho e Portões de Qualidade

- Cada agente trabalha em branch e worktree próprios. Dois agentes não editam a mesma árvore de
  trabalho ao mesmo tempo.
- Issues usam labels `area:*`, `tipo:*` e `agente:*`.
- Antes de começar, o agente confere `git status` e `git log` e para se achar alteração inesperada.
- Push exige confirmação humana.
- Nesta etapa, o responsável humano faz os commits e pushes, conforme sua orientação vigente.
- Portões antes de integrar: testes passam; o teste de rastreabilidade (I), o de parâmetros (II),
  o de reprodutibilidade (III), o caso à mão (VI) e o de queda de fonte (VII) passam; a checagem
  de segredos (VIII) passa.
- Toda devolutiva de agente registra: arquivos alterados, testes rodados com resultado e limitações.

## Governance

Esta constituição vale acima de qualquer outro documento de prática do projeto. Em conflito, ela
prevalece; `docs/PLANO.md` é histórico.

- Emenda: proposta por escrito, com o motivo e o efeito nas specs e planos existentes; aprovada
  pelo responsável humano do projeto; registrada com nova versão e data.
- Versão: semântica. MAJOR para remoção ou redefinição incompatível de princípio; MINOR para
  princípio ou seção nova, ou ampliação relevante; PATCH para esclarecimento de texto.
- Conformidade: toda spec, plano e revisão de integração confere os princípios I a IX. Desvio
  precisa de justificativa escrita no plano da feature e de aprovação humana.
- Guia de execução dos agentes: `CLAUDE.md` e `AGENTS.md`.

**Version**: 1.1.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
