Você está no repositório /home/pedrolucas/tellus (projeto Tellus). Objetivo desta sessão: primeira etapa do SDD com o GitHub Spec Kit, ou seja, grafo do repositório, constituição, mapa de features e uma spec por feature. NÃO execute /speckit.plan, /speckit.tasks, /speckit.analyze, /speckit.taskstoissues nem /speckit.implement, e não crie issues.

Leia antes: docs/sdd/RETORNO_INSTALACAO.md, REGISTRO.md, docs/pesquisa_chuva/RELATORIO.md, data/raw/zarc/FONTE.md, data/raw/conab/FONTE.md, Pesquisa_NASA_Agricultura_Agentes.md. O docs/PLANO.md é histórico: aproveite o método, descarte a arquitetura.

Regras
- O Spec Kit instalado é a 1.4.0, com os comandos instalados como skills. Onde este prompt diz /speckit.<comando>, use a skill correspondente (speckit-<comando>) conforme listada em .claude/skills/.
- Antes de começar, confira com `git status` e `git log -5` se não há outro agente ou sessão alterando o repositório (na instalação houve um commit e um push feitos em paralelo por outro processo). Se houver alteração inesperada, pare e registre no retorno.
- Specs em PT-BR, mantendo os nomes de seção dos templates do Spec Kit.
- Nunca leia ou exiba .env. Peça confirmação antes de push.
- Nenhum parâmetro agronômico ou econômico inventado. Valor sem fonte entra como requisito de "obter de fonte X" ou fica marcado [NEEDS CLARIFICATION].
- Não me faça perguntas durante a sessão. Toda dúvida vai para docs/sdd/DUVIDAS_ETAPA1.md (formato abaixo).

O produto
Tellus é uma aplicação web para o produtor rural de todo o Brasil. Ele localiza a lavoura de três formas: desenhando ou marcando no mapa, enviando arquivo georreferenciado (KML, KMZ, GeoJSON ou Shapefile .zip) ou informando o número do CAR. Depois informa a data exata de colheita da safra principal (soja no caso de referência), a textura do solo (arenosa, média ou argilosa; o app converte para a classe AD do ZARC e para mm, com fonte, e permite edição avançada em mm) e o grupo de cultivar (I, II, III ou "não sei", caso em que o app testa todos). O app oferece duas metodologias sobre o mesmo motor:
1. Cultura escolhida: devolve os melhores decêndios de plantio.
2. Cálculo completo: ordena culturas e decêndios e indica o melhor par.
O motor calcula, para cada cultura × decêndio dentro da janela ZARC, o risco de falta de água e a margem por hectare em cenários conservador, central e favorável (percentis da série histórica), e trata a entressafra (período entre a colheita e o plantio seguinte, incluindo a opção de deixar o solo em pousio ou cobri-lo).
Culturas da 2ª safra no caso de referência: milho, sorgo e planta de cobertura. A cobertura gera custo e um fator de lucro sobre a safra seguinte, editável e com fonte; sem fonte, aparece como hipótese.
Caso de referência para validação: Rio Verde/GO, onde já existem evidências no repositório.

Fontes de dados e decisões já tomadas
1. Chuva: IMERG Final V07 diário (GES DISC, Earthdata) é a fonte principal, por ter vencido a comparação contra a estação INMET A025 (viés -1,03%, MAE 4,13 mm/dia em 1.218 dias). INMET serve para validação local automática com a estação mais próxima, exibida na tela de fontes. Download sob demanda por célula de 0,1° com cache persistente e versionado; pré-carga opcional de regiões. A geometria da propriedade é cruzada com as células e a chuva é a média ponderada pela área de cada célula. O catálogo do IMERG Final consultado termina em set/2025; a latência e o tratamento do período recente são dúvida a registrar.
2. Clima: NASA POWER para temperatura, radiação, umidade e vento (ETo). A chuva do POWER não é usada.
3. Calendário: ZARC por município, cultura, solo, grupo de cultivar e decêndio, para todas as UFs, ingerido do SISZARC (o REGISTRO.md documenta a sequência de POST sem login). Nada fora da janela ZARC é sugerido como plantio.
4. Solo e culturas: capacidade de água, profundidade de raiz, fases, duração do ciclo, Kc e Ky. A base de referência será montada junto das specs, priorizando Embrapa e referências locais e usando FAO-56 e FAO-33 como método. Cada parâmetro precisa de fonte, data, unidade e validade regional.
5. Economia: custo operacional da Conab da praça mais próxima com a mesma cultura (mostrar a praça e a distância); preço padrão CEPEA/ESALQ quando houver; o produtor pode substituir qualquer premissa. A lista do que entra no custo fica visível.
6. Vegetação: MODIS e HLS como contexto do histórico da área (sazonalidade, cobertura), sem converter em produtividade.
7. Umidade do solo: SMAP como contexto regional, com aviso explícito da escala do produto.
CAR: não há API pública aberta que devolva o polígono pelo número. Caminho a validar: WFS de geoserver.car.gov.br por código do imóvel (usado pelo plugin QGIS "Consulta SICAR"). A spec deve prever o upload do shapefile do SICAR como alternativa.

Stack (vai para a constituição; as specs continuam sem detalhes de implementação)
Frontend Astro com Tailwind; backend Python gerenciado com uv; comunicação por contrato de API versionado. Implementação por Claude Code e Codex. Paleta e identidade visual ainda não existem: são uma feature própria e posterior ao fluxo funcional.

Passos
0. Crie a branch sdd/etapa-1 a partir de main.
1. Rode /graphify . respeitando as exclusões configuradas. Leia graphify-out/GRAPH_REPORT.md e use o grafo para navegar no repositório.
2. /speckit.constitution com estes princípios, cada um com regra verificável:
   - Rastreabilidade: todo número exibido traz fonte, versão do produto, período, unidade, localização ou célula e informação de qualidade.
   - Sem parâmetro inventado: valor sem fonte fica com status "hipotese" visível na interface e no contrato.
   - Reprodutibilidade: o mesmo pedido com o mesmo cache gera a mesma resposta; dados brutos são recriados por scripts e não são versionados.
   - Respeito à escala: resolução e limitação de cada produto aparecem junto do resultado; frequência histórica não é apresentada como previsão.
   - Premissas editáveis: o produtor pode substituir qualquer premissa econômica ou agronômica e ver o efeito.
   - Motor de cálculo puro, sem rede, testado contra pelo menos um caso calculado à mão.
   - Degradação explícita: fonte indisponível usa o cache e avisa com a data dele; sem cache, erro legível com a origem.
   - Segredos fora do Git; credenciais Earthdata só por variável de ambiente.
   - Restrições de stack e de idioma descritas acima; trabalho por branch e worktree por agente, issues com labels area:*, tipo:* e agente:*.
3. Crie docs/sdd/MAPA_FEATURES.md propondo a decomposição, com dependências e ordem. Ponto de partida, ajustável se você justificar: localizacao-propriedade; dados-clima (IMERG, INMET, POWER, cache, validação); calendario-zarc; base-solo-culturas; motor-hidrico-entressafra; economia; recomendacao (as duas metodologias); vegetacao-modis-hls; umidade-smap; contrato-api; interface-web (fluxo, mapa, fontes, premissas, estados de carga e erro); identidade-visual; pesquisa-car-wfs (tipo pesquisa).
4. Rode /speckit.specify para cada feature, na ordem do mapa. Cada spec descreve o quê e o porquê, com histórias de usuário priorizadas, requisitos funcionais testáveis, entidades, critérios de sucesso mensuráveis, fontes e unidades envolvidas e casos de borda (fora da janela ZARC, célula sem dado, geometria inválida, CAR inexistente, fonte fora do ar, município sem praça Conab). Se o Spec Kit criar uma branch por feature, ao final integre todas em sdd/etapa-1 para que as specs fiquem visíveis numa branch só.
5. Rode /speckit.clarify em cada spec sem responder às perguntas. Mantenha os marcadores [NEEDS CLARIFICATION] e registre cada pergunta em docs/sdd/DUVIDAS_ETAPA1.md no formato: ID | feature | pergunta | por que importa | opções | recomendação com justificativa | o que bloqueia.
6. Autoverificação, com o resultado registrado: nenhuma spec cita framework ou biblioteca; todo critério de sucesso é mensurável; toda constante tem fonte ou marcação; as duas metodologias usam o mesmo motor; as decisões acima aparecem nas specs certas.
7. Commite em sdd/etapa-1 em PT-BR, peça confirmação e faça push da branch. Não abra PR.

Retorno
Crie docs/sdd/RETORNO_ETAPA1.md contendo: o que foi feito, passo a passo, com os comandos usados; versão do Spec Kit; resumo da constituição; tabela de features (ID, nome, caminho da spec, dependências, número de requisitos, número de dúvidas); principais decisões de interpretação que você tomou sozinho; contagem e link para DUVIDAS_ETAPA1.md; resultado da autoverificação; desvios deste prompt e por quê; estado do Git (branch, commits, push). Commite e envie. Termine com: "Retorno salvo em docs/sdd/RETORNO_ETAPA1.md. Volte à conversa de planejamento para a revisão."
