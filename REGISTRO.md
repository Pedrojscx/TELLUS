# Registro nasa26
Prazo: dom 15/11/2026 12h BRT. Arquivo curto de decisões, evidências, bloqueios e próximos passos. Todo agente lê antes de agir e acrescenta ao fim.

## Ambiente (14/11 01h)
- Linux, 16 núcleos, 15 GB RAM (5,9 GB livres), 491 GB de disco.
- python 3.14, uv, node 26, git, gh, docker, codex-cli 0.154 (logado via ChatGPT), claude 2.1.325. Sem GDAL.
- Founder Skill: 11 skills em `.claude/skills/`. Reconhecidas.
- Maestri: AppImage em `~/Applications/Maestri.AppImage`. Não está aberto. CLI `maestri` fora do PATH nesta sessão.
- Sem credencial Earthdata (`~/.netrc` ausente).

## Evidências de dados NASA
- POWER diário, ponto -22.92,-45.46 (Pindamonhangaba-SP), 2015-01-01 a 2026-11-10: HTTP 200, 4332 dias, 1,8 s, sem login. `data/raw/power/`. Faltantes: só 3 dias de radiação. Fill value -999.
- POWER `IMERG_PRECTOT` mensal: todo -999 neste ponto. Não serve.
- MOD13Q1 NDVI (ORNL DAAC, 250 m, 16 dias): HTTP 200 sem login. `data/raw/modis/`. Escala 0.0001.
- HLS S30 v2.0 (CMR): busca sem login acha 14 cenas ago-nov/2026, 3 com nuvem <10%. Baixar exige Earthdata Login.

## Pendências
- Chuva POWER de 2025 = 643 mm, contra 930-1360 nos outros anos. Conferir com outra fonte antes de usar.
- Página do desafio Field Shift não abriu por fetch simples (conteúdo via JavaScript). Ler no navegador.
- Nenhum custo Conab ou regra ZARC consultado ainda.

## Decisões
- 14/11 01h15 — Ideia B escolhida pelo usuário: segunda safra (milho, sorgo ou cobertura) conforme data de colheita da soja, com margem por cenário. NDVI MODIS como camada extra. Região ainda aberta (candidata: Rio Verde-GO); fechar após achar custo Conab e ZARC do mesmo recorte.
- Maestri aberto pelo usuário às 01h15. A sessão que escreveu este registro até aqui roda fora do Maestri.

## Evidência Rio Verde-GO (14/11 01h30)
- POWER diário 1984-2026, ponto -17.80,-50.92: HTTP 200, 2,3 s. `data/raw/power/rioverde_go_*`.
- Chuva somada nos dias 45-85 após o plantio, 41 anos (janela é hipótese, sem fonte agronômica ainda): plantio 20/01 mediana 193 mm; 05/02 125 mm; 20/02 68 mm; 05/03 36 mm. O sinal da data de plantio é forte.
- ALERTA de validade: a chuva anual do POWER cai de mediana 1353 mm (1984-2024) para ~1000 mm em 2020-2024 e 678 mm em 2025. O mesmo ocorre em Pindamonhangaba. Suspeita: viés do produto nos anos recentes, não clima real. Conferir com estação INMET ou CHIRPS antes de mostrar anos recentes. Até lá, avisar na tela.

## Plano
- Escopo, método, contrato, agentes e cronograma em `docs/PLANO.md`.

## Sessão 14/11 (Claude Code) — pendências
- Chuva 2025 conferida com ERA5 (Open-Meteo, `data/raw/openmeteo/`): 892 mm contra 644 mm do POWER. As duas fontes dizem que 2025 foi seco, mas o tamanho difere. Em outros anos a diferença é maior (2015: 1118 POWER, 1711 ERA5; 2017: 1291 e 905). A célula do POWER tem altitude média de 854 m; a várzea fica perto de 540 m. Usar a chuva do POWER como ordem de ano seco/úmido, não como milímetros exatos.
- Conab (`data/raw/conab/`, 6 planilhas .xls, HTTP 200 sem login). Não há arroz irrigado de SP. Mais próximos em arroz irrigado, R$/ha, março/2026: Cachoeira do Sul-RS custo variável 9.746, total 13.478, 7.500 kg/ha; Pelotas-RS 11.063 e 14.674, 8.000 kg/ha. Massaranduba-SC 2025: 8.992 e 15.444, 7.750 kg/ha.
- Conab em SP: feijão 1ª safra Taquarituba 2026 (variável 9.538, total 15.175, 2.750 kg/ha). Soja Assis só até 2021, milho 2ª safra Assis só até 2023; milho 1ª safra sem SP. Soja e milho de SP atuais precisam de outra fonte (IEA) ou de praça vizinha (Londrina-PR 2026 existe para soja).
- ZARC (`data/raw/zarc/`). Arroz irrigado SP, Portaria 62/2020: Pindamonhangaba, semeadura nos períodos 28 a 36 (1º out a 31 dez), igual nos 3 grupos de cultivar e 3 solos. Arroz irrigado tropical, Portaria 397/2020: Pindamonhangaba, risco 20% nos períodos 22 a 4, 30% no 21, 40% em 19 a 20 (tabela do PDF quebrada, conferir no original). São as portarias que a pasta "safra vigente" do MAPA lista; ambas são de 2020.
- ZARC soja 2026/27 (Portaria 211/2026) e feijão 2026: a lista de municípios e janelas só está no SISZARC. Não consultado.
- Página do desafio Field Shift: ainda não lida. `curl` falha na verificação do certificado do site e a extensão do Chrome não estava ligada. Resumo de sites de eventos locais: ferramenta de apoio à decisão de rotação de culturas, com dados NASA, solo local, características das culturas e prioridades do produtor, para saúde do solo e adaptação.

## Próximos passos
- Ler o texto oficial do desafio no navegador.
- Fechar ideia e região (decisão humana). Custos Conab existem para arroz no RS/SC e feijão em SP; para o Vale do Paraíba só por aproximação.
- Consultar SISZARC para soja, milho e feijão em Pindamonhangaba.

## Conferência da chuva em Rio Verde-GO (14/11 01h50) — BLOQUEIO DE VALIDADE
Estação INMET A025 (medição em solo, -17.785,-50.965) contra POWER PRECTOTCORR. Arquivos em `data/raw/conferencia/`.
| Ano | INMET mm | cobertura | POWER mm | ERA5 mm | POWER/INMET |
|---|---|---|---|---|---|
| 2008 | 1713 | 0,99 | 1373 | 1499 | 0,80 |
| 2012 | 1381 | 0,96 | 1126 | 1268 | 0,82 |
| 2016 | 1357 | 0,90 | 1075 | 1403 | 0,79 |
| 2019 | 1108 | 0,91 | 1265 | 935 | 1,14 |
| 2022 | 1326 | 1,00 | 977 | 790 | 0,74 |
| 2024 | 1461 | 0,62 | 1012 | 1000 | 0,69 |
| 2025 | 1548 | 1,00 | 678 | 731 | 0,44 |
- Conclusão: a chuva do POWER fica cerca de 20% abaixo da estação até 2016 e 26-56% abaixo em 2022-2025. De janeiro a abril de 2025 a estação mediu 898 mm e o POWER deu 409 mm. Usar a chuva do POWER sem correção exagera o risco de seca.
- Limites: uma estação contra uma grade de 50 km; 2024 tem 38% de horas sem dado. Só 7 anos conferidos.
- ERA5 (Open-Meteo, não é NASA) também fica baixo nos anos recentes. Não serve de árbitro.
- Nota: o portal do INMET recusou o curl padrão; o download funcionou com User-Agent de navegador. São dados públicos abertos.
- Opções: (1) IMERG Final da NASA, calibrado por pluviômetros, 0,1°, desde 2000 — exige Earthdata Login do usuário; (2) corrigir a chuva do POWER por mês com a estação INMET e mostrar a correção; (3) usar chuva do INMET e POWER só para temperatura, radiação e ETo.
- Decisão provisória (H): fonte de chuva plugável em `app/dados/`. Começar com (2), trocar por (1) se o login chegar e o teste passar. A comparação com a estação vira parte da tela de fontes.

## Founder Board (14/11 01h45)
- 3 × "construir se", nota 6. Resumo e condições em `founder/board.md`. Região fechada em Rio Verde-GO.

## Maestri
- A sessão que escreveu até aqui não tem o CLI `maestri`. A orquestração tem de sair da sessão aberta dentro do Maestri.
- Próximos passos do Maestro: (a) `maestri list`, `maestri preset list`, `maestri floor list`; (b) delegação de teste a um Codex: criar `app/__init__.py` e `pyproject.toml` com uv, fastapi, pytest, e devolver por ask back; (c) conferir o commit; (d) só então ativar a etapa 1 de `docs/PLANO.md`.

## Conab e ZARC de Rio Verde-GO (14/11, Claude Code) — pendência fechada
Nota: a seção "Sessão 14/11 (Claude Code) — pendências" acima foi escrita antes de eu ver que a região fechou em Rio Verde. Os dados de SP ali ficam só como registro.
- Conab, abas "Rio Verde-GO-2026", março/2026, R$/ha, plantio direto, em `data/raw/conab/`:
| Cultura | Produtividade kg/ha | Custeio | Custo variável | Custo operacional | Custo total |
|---|---|---|---|---|---|
| Soja 1ª safra 2026/27 | 3.900 | 3.354 | 4.096 | 5.152 | 6.129 |
| Milho 2ª safra 2026 | 6.000 | 3.804 | 4.819 | 5.889 | 6.886 |
| Sorgo granífero 2ª safra 2026 | 3.600 | 2.259 | 2.807 | 3.807 | 4.788 |
- Custo total inclui depreciação, arrendamento e remuneração de terra e capital. A produtividade é a premissa da Conab (ex-ante), não medição. Não há planilha Conab para planta de cobertura.
- ZARC 2026/27, Rio Verde, sequeiro, GRUPO I de cultivar, do SISZARC (`data/raw/zarc/siszarc_GO_*.xls`). Decêndio 1 = 1 a 10 de janeiro.
  - Milho 2ª safra (Portaria 322): risco 20% nos decêndios 1 a 3. Decêndio 4 (1 a 10 fev): 40% em AD1, 30% em AD2 e AD3, 20% em AD4 a AD6. Decêndio 5: 40% AD4, 30% AD5, 20% AD6. Decêndio 6 (21 a 28 fev): só AD6, 30%. Depois disso, fora da janela.
  - Milho com braquiária (Portaria 337): janela igual à do milho.
  - Sorgo granífero 2ª safra (Portaria 273): solo arenoso até o decêndio 6 (40%); textura média até o 7 (30%); argiloso 20% até o 8 e 30% no 9 (21 a 31 mar).
  - Soja (Portaria 198): decêndios 28 a 36 e 1 (1º out a 10 jan); 27 com 40% em AD3 a AD6.
- Leitura para o produto: o sorgo aceita plantio cerca de um mês depois do milho. Isso apoia a ideia B com fonte oficial.
- Falta: grupos II e III de cultivar (o script baixou só o GRUPO I); preço de venda (Conab não traz); custo de cobertura.
- SISZARC responde a POST simples sem login. Sequência: `carregarComboCulturas` → `OutrosManejos` → `Clima` → `Ufs` → `Portarias` → `Grupos` → `Solos` → `gerarRelatorioXLS`, sempre em `gerarRelatorioPublicacoesDoZarc!<ação>.action`.
- Texto oficial do desafio Field Shift continua sem leitura (certificado falha no curl; extensão do Chrome desligada).

## IMERG com token Earthdata (14/11, Claude Code) — BLOQUEIO
- Token Earthdata do usuário guardado em `.env` (`EARTHDATA_TOKEN`, permissão 600, ignorado pelo Git). Vale até 13/01/2027. Nunca commitar.
- `gpm1.gesdisc.eosdis.nasa.gov` (OPeNDAP antigo): respondeu `.dds` (só metadados) e depois passou a recusar conexão (porta 443, IPv4 e IPv6). Nenhum valor de chuva foi baixado. Arquivo parcial apagado.
- Caminho atual, achado pelo CMR: `https://opendap.earthdata.nasa.gov/collections/C2723754851-GES_DISC/granules/<GranuleUR>` (IMERG mensal V07B) e download direto em `data.gesdisc.earthdata.nasa.gov`. Variáveis no grupo `/Grid/`.
- Os dois dão 403 "EULA Acceptance Failure". O usuário precisa autorizar a aplicação "NASA GESDISC DATA ARCHIVE" no perfil Earthdata (https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ). Depois, refazer a série mensal 2000-2026 no ponto da estação A025 e comparar com `data/raw/conferencia/inmet_a025_mensal.json` (já pronto, 80 meses).

## ZARC grupos II e III, Rio Verde (14/11)
- Milho 2ª safra, GRUPO II: janela mais curta que o GRUPO I. 20% só até 10/jan (AD1) ou 20/jan (AD3, AD4); AD6 vai até o decêndio 5 com 40%.
- Sorgo 2ª safra: GRUPO II argiloso até o decêndio 8 (40%); GRUPO III argiloso até o 6 (40%). Ciclo mais longo encurta a janela.

## Pesquisa reproduzível de chuva — 14/11/2026 (Codex)
- Relatório: `docs/pesquisa_chuva/RELATORIO.md`. Scripts em `scripts/chuva_*.py`, CSV e metadados em `data/processed/pesquisa_chuva/`, respostas e NetCDF em `data/raw/pesquisa_chuva/`. Sem commit/push.
- O bloqueio IMERG registrado antes NÃO se repetiu: acesso autenticado oficial funcionou. Coleção diária GPM_3IMERGDF V07 / V07B, C2723754864-GES_DISC. DAP2 `.dds` retorna 400 por Int8; DAP4 `.dap.nc4` funciona. Obtidos 1.363 dias: jan–jun de 2008, 2012, 2016, 2019, 2022, 2024 e 2025, mais jul–set/2025. Todos com precipitation_cnt=48 na célula. Out–dez/2025: 92 respostas 404; catálogo consultado termina em setembro/2025. Nenhum segredo nos resultados.
- INMET A025: coordenadas do CSV -17,78527777, -50,965, 780,11 m. Chuva horária encerra na hora da mensagem; dia UTC soma registros 01h–00h seguinte. Exigidas 24 horas válidas. Dos 2.559 dias dos sete anos, 2.267 pareiam com POWER e 292 são excluídos. Jan–jun: 1.218/1.271 dias. Nenhum ano completo; só jan–jun/2019 completo. Não chamar somas parciais de totais anuais.
- O ponto antigo POWER (-17,80,-50,92), a 5,04 km da estação, consulta outra célula. Igualdade dos 31 valores de jan/2025 confirma centro antigo (-18,-50,625) e centro da consulta à estação (-18,-51,25). IMERG usa centro (-17,75,-50,95), a 4,23 km da estação. Escalas de grade não equivalem ao pluviômetro.
- Jan–jun, mesmas 1.218 datas: INMET 6.349,60 mm; IMERG 6.284,47 mm (viés -1,03%, MAE 4,13 e RMSE 8,59 mm/dia); POWER na estação 4.637,61 mm (-26,96%, MAE 4,53 e RMSE 9,85 mm/dia). Dias ≥1 mm: INMET 35,14%, IMERG 44,50%, POWER 50,00%. Viés agregado IMERG esconde +25,64% em 2012 e -19,50% em 2025.
- Jan–jun/2025, 180 dias pareados: INMET 969,20 mm; IMERG 780,19; POWER na estação 392,16; ponto antigo POWER 426,90. Dia 21/01 excluído por ter 23 horas. No ano, 357 dias pareados: INMET 1.534,00 mm, POWER estação 628,52, ponto antigo 676,48; não são totais anuais completos.
- Correção mensal POWER: ajuste 2008/2012/2016/2019; avaliação 2022/2024/2025; ≥95% dos dias por mês e pelo menos três meses-ano no ajuste. Março/julho sem fator. Em 328 dias de avaliação jan–jun, viés passa de -49,62% para -46,65%, MAE piora de 4,87 para 4,93 mm/dia. Não validada para uso agrícola; volumes corrigidos não corrigem ocorrência.
- Recomendação desta pesquisa atualiza a hipótese do plano: INMET como referência local com controle; IMERG Final como melhor candidato de grade para simular o histórico, com viés local e falhas visíveis; não adotar POWER corrigido automaticamente. Frequência histórica não é previsão.
- Não há modelo agrícola executável ou parâmetros rastreáveis de solo/Kc/Ky/fases/inicialização neste estado do projeto. Não calculados déficit, produtividade, margem nem ranking milho/sorgo/cobertura. Faltam validação da estação e vizinhas, continuidade histórica, parâmetros agronômicos e preços locais. Não foi demonstrado se a fonte muda a escolha agrícola.
- Verificações passaram: unidades, datas/horas únicas e calendário, ausências, contagens IMERG, somas pareadas, separação de ajuste/teste, checagem independente de quatro dias INMET e igualdade do recorte IMERG com o arquivo global. Gráficos revisados. Reprodução sem rede: executar `chuva_analise.py`, `chuva_comparar_imerg.py`, `chuva_verificar.py` e `chuva_relatorio.py` com o ambiente de `scripts/requirements-chuva.txt`.

## Spec 001 — localização (14/11, 23h10, LK + Claude Code)
- Constituição v1.0.0 e mapa das specs 001 a 012 em `docs/sdd/MAPA_SPECS.md`. Specs 002 a 007 escritas, cada uma na sua branch.
- 001 implementada na branch `001-localizacao`: backend FastAPI em `backend/` (pacote `tellus`, uv), frontend Astro 7 + Tailwind 4 + Leaflet em `frontend/`, referências em `referencias/localizacao/` geradas por `scripts/preparar_localizacao.py`.
- Fontes testadas: IBGE localidades (5.571 municípios) e malha mínima (5.570 polígonos; falta Boa Esperança do Norte-MT, 5101837, município novo); INMET `estacoes/T` (668 automáticas, 534 operantes); Conab soja, milho 2ª safra e sorgo (27 praças com planilha de 2025/26; sorgo só em 4: Barreiras-BA, Rio Verde-GO, Uberaba-MG, Pedro Afonso-TO).
- A planilha de milho 2ª safra fica em `.../agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls`; o link da página termina em `/view` e devolve HTML.
- Células: POWER = round(lat/0,5)·0,5 e round(lon/0,625)·0,625; IMERG = centro da célula de 0,1°. Ambas conferem com os centros do REGISTRO e da pesquisa de chuva.
- 50 testes pytest passando: Rio Verde confere com o REGISTRO (A025 a 0 km, IMERG -17,75/-50,95, POWER -18/-51,25, praça Rio Verde com as 3 culturas), 10 capitais certas, recusas, determinismo, desempenho.
- A malha mínima simplifica costa e ilhas: um ponto até 2 km fora do contorno usa o município mais próximo, com aviso.
- Pendente: teste de tela manual do quickstart (passo 4) e cronômetro do SC-001.

## Reconciliação dos planos (14/11, 23h40, LK + Claude Code)
- O LK e o Pedro escreveram specs em paralelo. Decisão do LK: o plano do Pedro (`sdd/etapa-1`, 13 specs, 59 issues) é o oficial e foi mergeado na `main`.
- Constituição 1.1.0 = a do Pedro + "Decisões de Dados e Escopo" (chuva do POWER fora do balanço, cobertura nacional com referência mais próxima declarada, escopo até o prazo).
- A antiga 001-localizacao do LK virou `specs/002-localizacao-propriedade/entrega-1-ponto/` (código e testes na `main`). As specs 002 a 007 do LK ficam como consulta (`docs/sdd/MAPA_SPECS.md`).
- Divisão proposta em `docs/sdd/SINCRONIA_PEDRO.md`: LK fica com a 003 dados-clima; Pedro com a 004 e a 005.
