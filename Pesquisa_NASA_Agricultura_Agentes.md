# Pesquisa para o projeto nasa26
Atualizada em 14/11/2026. Prazo de desenvolvimento informado pelo usuário — 15/11/2026 às 12h, horário de Brasília.

## Objetivo confirmado
Construir um app funcional com dados reais da NASA que ajude agricultores a escolher estratégias de rotação com potencial de melhorar o resultado econômico. A região será escolhida pela relevância do problema, disponibilidade dos dados e possibilidade de validação. Vale do Paraíba é candidato. Equipe de cinco pessoas, atribuições humanas a definir posteriormente. Execução em um computador Linux com Maestri instalado, Claude Pro e ChatGPT Plus. Prioridade a ferramentas gratuitas. Hospedagem será decidida posteriormente.

Este documento reúne pesquisa documental, hipóteses e testes necessários. As propostas de arquitetura, prioridades e prazos abaixo são recomendações de trabalho. O acesso programático aos dados ainda exige testes locais. Uma tentativa de consultar NASA POWER neste ambiente falhou por resolução de DNS.

## 1. Decisão agrícola e resultado econômico
Pergunta de produto proposta — qual sequência de culturas faz sentido para esta área, considerando água, calendário, custos, mercado e risco?

O app deve permitir comparar o manejo atual com alternativas plausíveis e mostrar o motivo das diferenças. A decisão escolhida precisa ocorrer de fato na rotina do produtor. Investigar quem decide, quando decide, que informação usa, qual erro custa mais e quais limitações impedem uma mudança.

A rotação precisa ocupar um horizonte de várias safras. A Embrapa distingue rotação e sucessão dentro do mesmo ano agrícola. A comparação deve considerar máquinas disponíveis, histórico da área e exigências das culturas. [Embrapa — rotação](https://www.embrapa.br/web/agencia-de-informacao-tecnologica/cultivos/soja/producao/manejo-do-solo/rotacao-de-culturas) · [Embrapa — planejamento dos sistemas](https://www.embrapa.br/en/web/agencia-de-informacao-tecnologica/cultivos/cevada/producao/rotacao-de-culturas)

Modelo econômico inicial proposto, sujeito a validação:
- Receita por hectare = produtividade do cenário × preço recebido pelo produtor.
- Margem por hectare = receita − custos explicitamente incluídos.
- Comparar as alternativas no mesmo período e com os mesmos critérios de custo.
- Separar cenários conservador, central e favorável com premissas editáveis.
- Incluir sementes, fertilizantes, operações, irrigação quando aplicável, colheita, transporte e custo de transição.
- Explicar se custos fixos e custo da terra estão incluídos antes de chamar o resultado de lucro líquido.
- Calcular o preço e a produtividade de equilíbrio quando os dados permitirem.
- Benefícios futuros da cobertura do solo exigem evidência e horizonte temporal explícitos.
- Uma distribuição de probabilidades ou retorno esperado exige calibração. Uma nota de estresse da vegetação, sozinha, não fornece a perda financeira.

A Conab oferece planilhas e metodologia de custos para diversas culturas. Cada registro deve guardar região, safra, sistema produtivo e unidade. Preços de referência precisam ser ajustados ao mercado do produtor, ao frete e à data. O CEPEA informa referências por praça e metodologia, cuja reutilização e acesso deverão ser verificados. A leitura direta do site foi limitada nesta pesquisa. [Conab — custos](https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao) · [Planilhas](https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao/planilhas-de-custos-de-producao) · [CEPEA — metodologia milho](https://cepea.org.br/br/metodologia/metodologia-de-precos-do-milho-npr.aspx)

## 2. Regiões e problemas a comparar
A seleção geográfica continua aberta. Os candidatos abaixo são hipóteses para investigação, sem ranking econômico calculado.

| Candidato | Decisão a investigar | Evidência ou trabalho pendente |
|---|---|---|
| Vale do Paraíba, arroz e alternativas de rotação | Como diversificar mantendo compatibilidade com a água e a drenagem disponíveis | O IEA documenta concentração da produção paulista de arroz nas regionais de Guaratinguetá e Pindamonhangaba. Validar custos e alternativas com técnico local |
| Paraná, sistema de grãos | Como comparar rotações de várias safras considerando janela, clima e margem | Selecionar município com dados de culturas e custos compatíveis e consultar recomendações regionais |
| Mato Grosso ou Goiás, sistema de grãos | Como comparar alternativas da segunda safra dentro de um plano de rotação | Verificar calendários, limitações de água, mercado local, custos e evidência agronômica |
| Região com produtor acessível | Resolver uma escolha real relatada pelo usuário | Entrevista e dados da propriedade podem definir o recorte mais útil |

Escolher a região após conseguir um exemplo completo de dados NASA, custo comparável e sequência agrícola defensável. A disponibilidade de um produtor disposto a validar tem peso alto. [IEA — levantamento 2025/26](https://iea.agricultura.sp.gov.br/OuT/LerTexto.php?codTexto=16321)

## 3. Dados da NASA como núcleo
Proposta para a primeira prova técnica — NASA POWER para séries climáticas e um produto de observação da Terra, preferencialmente HLS/Landsat, IMERG ou SMAP, escolhido conforme a decisão agrícola. Cada indicador deve mostrar produto, versão, período, unidade, localização e qualidade. A participação da NASA deve ser visível no cálculo e na explicação da comparação.

| Fonte | Uso a testar | Questões de implementação |
|---|---|---|
| NASA POWER | Histórico de chuva, temperatura e condições de cultivo | Testar API diária, parâmetros, unidades, valores ausentes e resolução do produto de origem |
| HLS, NASA/USGS Landsat e Sentinel harmonizados | Evolução da vegetação e cobertura em área selecionada | Obter cena ou série real, aplicar máscara de qualidade, tratar nuvens e calcular índice com escala correta |
| GPM/IMERG | Distribuição das chuvas e períodos secos históricos | Escolher versão Early/Late/Final, verificar unidades e agregação temporal |
| SMAP | Contexto regional de umidade do solo | Escolher produto L3/L4, documentar grade e natureza observacional/modelada |
| ECOSTRESS | Estresse térmico e evapotranspiração | Verificar cenas disponíveis, qualidade, acesso e custo de processamento |
| SRTM | Relevo e condicionantes de escoamento | Testar recorte e derivação de declividade |
| MODIS/VIIRS | Séries de vegetação em áreas maiores | Verificar produto, escala, qualidade e mistura de pixels |
| GLDAS/NLDAS | Contexto de água e energia na superfície | Verificar cobertura geográfica do produto e adequação ao Brasil |
| GEDI | Estrutura de vegetação quando relevante ao caso | Exigir justificativa agrícola específica antes de integrar |

POWER reúne dados de observações e modelos. Sua meteorologia documentada utiliza MERRA-2. A proveniência deve acompanhar cada variável. A documentação atual também descreve alternativas de maior resolução para determinados parâmetros, cuja disponibilidade precisa ser confirmada na consulta usada. [POWER](https://power.larc.nasa.gov/) · [API diária](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) · [Origem meteorológica](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) · [Guia de acesso](https://power.larc.nasa.gov/docs/tutorials/data-access-viewer/user-guide/)

HLS fornece produtos harmonizados de refletância e índices de vegetação, distribuídos como GeoTIFF otimizado para nuvem. O acesso oficial descrito requer Earthdata Login. Nuvens e qualidade determinam quantas observações são realmente utilizáveis em cada área. [NASA HLS — acesso](https://hls.gsfc.nasa.gov/data-access-and-tools/) · [NASA HLS — informações técnicas](https://www.earthdata.nasa.gov/s3fs-public/2024-01/hls_fact_sheet_1-26-2-24.pdf)

IMERG possui produtos em grade de 0,1° e intervalos de meia hora. SMAP possui produtos com grades de 9 e 36 km. A aplicação precisa preservar a escala real do dado na interpretação da propriedade. [NASA — IMERG](https://search.earthdata.nasa.gov/search?q=GPM_3IMERGM_07) · [NASA — produtos SMAP](https://forum.earthdata.nasa.gov/viewtopic.php?t=5728)

### Teste de aceitação de uma fonte
1. Obter um arquivo ou resposta real para uma área brasileira e período explícito.
2. Salvar consulta, identificação do produto, data de obtenção e resposta original.
3. Conferir unidades, dados ausentes, fator de escala, qualidade e coordenadas.
4. Produzir um indicador reproduzível e confrontar com uma segunda leitura da fonte.
5. Mostrar como esse indicador altera uma comparação agrícola.
6. Manter cópia real previamente obtida para a demonstração, exibindo sua data.
7. Testar erro de rede, ausência de cobertura e expiração de credenciais.

A série histórica ajuda a construir contexto climático. Uma previsão futura exige produto e metodologia próprios. NDVI e umidade regional precisam de interpretação agronômica antes de alimentar hipóteses de produtividade.

## 4. Fontes complementares
As fontes locais conectam os dados NASA ao cultivo, ao solo e ao resultado econômico.

| Fonte | Contribuição | Pendência |
|---|---|---|
| Embrapa, IAC, CATI | Sequências de culturas, manejo e restrições | Selecionar referências específicas para culturas e região escolhidas |
| ZARC | Janelas por município, cultura, solo e cultivar | Extrair o recorte vigente, guardar versão e validar interpretação |
| IBGE/PAM | Área, produção e rendimento municipal | Consultar metadados e período da tabela antes de obter valores |
| Conab | Custos por cultura e localidade | Escolher sistema compatível e documentar ajustes |
| Produtor | Custo real, histórico, infraestrutura, objetivo e preço local | Entrevista e autorização para usar informações |
| SoilGrids | Propriedades do solo como contexto modelado | API REST anunciada como suspensa. Avaliar download alternativo ou dados locais |
| MapBiomas | Histórico de cobertura e uso da terra | Confirmar coleção, classes e resolução adequadas |

O ZARC permite consultar períodos de plantio com filtros de cultura, solo e outras condições. O SISZARC documenta exportação de relatórios. A API do IBGE fornece metadados, períodos e variáveis dos agregados. [ZARC](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/painel-de-indicacao-de-riscos-1) · [SISZARC](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/siszarc) · [API IBGE](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)

A documentação ISRIC informa suspensão temporária da API REST. MapBiomas oferece cobertura e uso do solo em produtos com diferentes resoluções. [ISRIC](https://docs.isric.org/globaldata/soilgrids/) · [MapBiomas 30 m](https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/)

Da lista original, WSS, SSURGO/STATSGO2, CDL, PRISM, NAIP, NLCD, USDA QuickStats/AMS e LANDFIRE exigem atenção à cobertura e ao contexto norte-americano. OpenET e CoCoRaHS também exigem checagem geográfica. Ag Data Commons e GAEZ dependem do conjunto selecionado. ERA5 e Sentinel-2 podem complementar a análise. A auditoria produto a produto dessas fontes fica condicionada à escolha do caso de uso.

## 5. Orquestração no Maestri
O Maestri documenta comunicação entre CLIs por conexões e uma skill própria. O modo Maestro permite recrutar agentes, atribuir papéis e conectar notas. Equipes mistas podem ser solicitadas explicitamente. Esses recursos devem ser testados na versão Linux instalada. [Conexões](https://www.themaestri.app/pt-br/docs/connections) · [Modo Maestro](https://www.themaestri.app/pt-br/docs/maestro) · [Linux](https://www.themaestri.app/pt-br/linux)

Proposta inicial de responsabilidades, sem atribuir superioridade universal a um modelo:

| Papel | Ferramenta inicial sugerida | Entrega verificável |
|---|---|---|
| Maestro e integração | Claude Code | Plano, contratos, distribuição e versão integrada |
| Pesquisa NASA e processamento | Codex | Adaptador de dados reais, metadados e indicador reproduzível |
| Regras agrícolas e economia | Claude Code | Regras com fontes, premissas e cálculos auditáveis |
| Interface | Codex | Fluxo utilizável e estados de carregamento/erro |
| Revisão e testes | Alternar ferramenta em relação ao autor | Relato de falhas e testes dos fluxos integrados |

Começar com dois executores simultâneos e o Maestro acionado nos pontos de decisão é uma proposta conservadora para calibrar consumo e memória. Papéis podem ser ativados em etapas. Conferir limites na conta antes de aumentar a concorrência.

Cada tarefa deve conter objetivo, entradas, dependências, arquivos sob responsabilidade, critério de aceite e formato da devolutiva. Um responsável integra alterações. Toda devolutiva registra arquivos/commit, testes executados, resultado e limitações.

Os Andares documentam isolamento por worktrees Git. Com isolamento desativado, os terminais compartilham a pasta. Verificar esse estado antes de edição paralela. O suporte a cópia instantânea depende do sistema de arquivos. [Andares](https://www.themaestri.app/pt-br/docs/floors) · [Worktrees Claude Code](https://code.claude.com/docs/en/common-workflows)

Prova operacional necessária — criar uma tarefa pequena, delegar de Claude Code para Codex, obter resposta, revisar mudança e integrar. O chat web do Claude fornece orientação e prompts. A execução local depende dos terminais, ferramentas e conexões disponibilizados no Maestri.

Claude e Claude Code compartilham limites de uso. O plano Pro também tem limites temporais. Conferir o consumo de Codex no plano Plus durante o trabalho. Registrar resultados curtos e reutilizar arquivos de contexto ajuda a controlar o volume. [Claude — planos e uso](https://support.claude.com/pt/articles/11145838-use-claude-code-com-seus-planos-pro-max-ou-ultra) · [Codex — planos](https://developers.openai.com/pt-BR/docs/pricing)

## 6. Founder Skill e Context Mode
Founder Skill foi instalado localmente com 11 comandos reconhecidos pelo Claude Code. O primeiro uso proposto é avaliar valor para o produtor, diferenciação e facilidade de uso das ideias candidatas. Entrevistas reais devem fundamentar a validação. Simulações de consumidores geram hipóteses. A avaliação comercial deve ser adaptada ao prazo e ao objetivo do hackathon. [Repositório Founder](https://github.com/Jakeschincariol/founder-skill)

O pacote solicitado @context-mode/cli configura um gateway externo para requisições dos agentes. Sua documentação descreve login e alterações de configuração. A instalação tentada anteriormente falhou por DNS. A ativação continua pendente. Sua compatibilidade com autenticação, ferramentas e Maestri precisa ser confirmada antes de virar dependência do fluxo. [CLI Context Mode](https://contextmode.ai/docs/cli)

## 7. Arquitetura e testes a decidir
Comparar uma implementação web simples com backend único e uma aplicação Python com interface rápida. Escolher pela prova de integração dos dados e experiência necessária. Proposta inicial — regras e cálculos determinísticos, dados de referência versionados, cache local e interface de comparação. Avaliar IA no produto apenas se houver benefício específico e acesso adequado.

Pesquisar e testar:
- Contrato de dados entre processamento, cálculo e interface.
- Identificação da área por coordenadas, município ou polígono.
- Harmonização temporal, sistema de coordenadas e agregação espacial.
- Estratégia de cache, timeout e repetição limitada de consultas.
- Limites do computador, tamanho dos recortes e tempo de processamento.
- Credenciais no backend e ausência de segredos no repositório.
- Testes de unidades, custos, campos ausentes e alternativas incompatíveis.
- Comparação completa com dados reais, erro de API e restauração da demonstração.
- Instalação reproduzível em ambiente limpo e comando de inicialização.
- Registro das fontes e explicações junto dos resultados.

## 8. Critérios de entrega e agenda sugerida
Até domingo às 12h, a proposta de aceite é um fluxo completo com dados NASA reais, comparação de alternativas, premissas econômicas editáveis, explicação dos indicadores e execução local reproduzível. A banca deve conseguir identificar de onde veio cada número e que decisão ele apoia.

Reservar inicialmente até 90 minutos para escolher o caso e provar acesso ao dado principal. Em seguida, estabelecer contratos e executar dados/cálculo e interface em paralelo. Priorizar integração ao longo de sábado. Reservar domingo de manhã para correções, validação da demonstração e documentação. Esses intervalos são uma proposta e precisam ser reajustados ao horário efetivo de início.

A página geral do evento informa submissão até 15/11 às 23h59 locais. O prazo de trabalho do usuário continua sendo 12h. A página local de Ajmer lista impacto, criatividade, validade, relevância e apresentação como critérios. Confirmar o guia global de 2026 e as exigências do evento local antes da entrega, incluindo registro de uso de IA, formato e links. [Evento 2026](https://www.spaceappschallenge.org/2026/) · [Critérios publicados pelo evento de Ajmer](https://www.spaceappschallenge.org/2026/local-events/ajmer/) · [Desafio Field Shift](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)

## 9. Pesquisas restantes por prioridade
| Prioridade | Pergunta | Evidência para encerrar |
|---|---|---|
| Imediata | Qual decisão agrícola tem maior valor e cabe no prazo? | Entrevista curta, comparação de 3 ideias e escolha fundamentada |
| Imediata | Qual produto NASA será usado de verdade? | Arquivo/resposta real processada e indicador demonstrado |
| Imediata | Qual região oferece o melhor caso verificável? | Dados, custo e referência agrícola para o mesmo recorte |
| Imediata | Como os agentes se comunicam e integram no Linux? | Delegação e integração completas no Maestri instalado |
| Antes de recomendar | Quais rotações são viáveis? | Referências regionais, restrições e revisão técnica |
| Antes de mostrar retorno | Quais custos, preços e produtividades são defensáveis? | Fontes, datas, unidades e cenários editáveis |
| Antes da apresentação | O app funciona quando uma fonte falha? | Teste com cache real e mensagem de estado |
| Antes da submissão | Quais são as exigências oficiais vigentes? | Guia global e instruções do evento local |
| Após o fluxo principal | Quais dados adicionais mudam uma decisão? | Comparação com e sem a camada proposta |
| Após a validação inicial | Como medir ganho econômico real? | Piloto com produtor e comparação longitudinal |

Não foram calculados ganhos financeiros, validada uma rotação para uma propriedade, consultada uma amostra completa de custos ou concluído um teste de integração NASA. A escolha final deve usar essas verificações, com escopo ajustado ao tempo restante.

