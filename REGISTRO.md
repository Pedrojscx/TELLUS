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

## CAR por WFS: D-001 respondida (15/11, 00h, LK + Claude Code)
- `https://geoserver.car.gov.br/geoserver/sicar/wfs` (WFS 2.0, sem login) tem uma camada por UF: `sicar:sicar_imoveis_<uf>`. Campos: cod_imovel, status_imovel, dat_criacao, data_atualizacao, area (ha), condicao, uf, municipio, cod_municipio_ibge, m_fiscal, tipo_imovel e geo_area_imovel (MultiPolygon). Não traz nome do proprietário.
- Consulta por código: `request=GetFeature&typeNames=sicar:sicar_imoveis_go&outputFormat=application/json&cql_filter=cod_imovel='GO-5218805-8F8B1082570B4C1799ADBEE6CE0EEE33'` devolve 1 feição em 0,35 s. Código inexistente devolve `numberMatched: 0`, distinto de fonte fora do ar.
- Consulta por área: `bbox=lonmin,latmin,lonmax,latmax,EPSG:4326` (ordem lon,lat). Ex.: 27 imóveis em 0,05° × 0,05° perto de Rio Verde.
- O prefixo do código (UF) escolhe a camada. Por regra da spec 001, a geometria ainda precisa de confirmação do produtor.
- Outros sites sugeridos: geo.cati.sp.gov.br (portal ArcGIS da CATI) e datageo.ambiente.sp.gov.br (GeoServer da SIMA). Ambos só cobrem SP e não servem para Rio Verde-GO. Não fazem parte do plano.

## Spec 003 dados-clima (15/11, 00h10, LK + Claude Code)
- Branch `003-dados-clima`: módulo `tellus.clima`, com o cliente IMERG (DAP4 `.dap.nc4` lido por h5py, cache por célula em `data/raw/clima/imerg/`), o cliente POWER (um pedido para o período), regras puras e rotas `/api/clima/{resumo,serie,validacao}`.
- IMERG de Rio Verde (célula -17,75/-50,95): 9.039 dias ok de 2001-01-01 a 2025-09-30 e 410 `nao_publicado` depois (D-002: lacuna recusada, aviso `lacuna_imerg`). Download de cerca de 20 min com 16 conexões.
- POWER (célula -18/-51,25, 731,58 m): 9.449 dias, sem -999. Fontes MERRA2, GEOSIT, SYN1DEG e POWER.
- SC-002 reproduzido de forma independente (IMERG baixado de novo contra a série INMET da pesquisa): 1.218 dias jan–jun; IMERG 6.284,48 mm, viés -1,03%, MAE 4,13, RMSE 8,59 mm/dia; POWER -26,96%.
- `referencias/clima/rio_verde_go/` (série derivada, meta com sha256): a demo roda sem rede. Sem cache, o serviço cai nela (`origem_dados: referencia_versionada`).
- A API de dados por estação do INMET (`apitempo.../estacao/...`) responde 204. Só a A025 tem validação; as outras estações recebem `disponivel: false` com o motivo.
- 68 testes passando (pytest com `--import-mode=importlib`).

## Spec 001 CAR (15/11, 00h40, LK + Claude Code)
- Branch `001-pesquisa-car-wfs`: módulo `tellus.car` (regras puras de geometria, cliente WFS com cache, leitor de shapefile com pyshp) e as rotas `GET /api/car/{codigo}`, `POST /api/car/upload` e `POST /api/lavoura/confirmar`. Na tela: campo do CAR, polígono no mapa, upload SICAR e botão de confirmar.
- Estados: encontrado, inexistente, sem_geometria, geometria_invalida, codigo_invalido e fonte_indisponivel. Com cache e fonte fora do ar, devolve o estado guardado com o aviso `cache_usado`.
- TLS: o servidor do SICAR só negocia cifras que o OpenSSL 3.5 (Python 3.14) recusa por padrão. O cliente usa `DEFAULT:@SECLEVEL=1` com o certificado verificado. Sem isso, a consulta caía em `fonte_indisponivel`.
- Ao vivo: GO-5218805-8F8B…EE33 → encontrado em 0,67 s, 35,15 ha calculados contra 35,0003 ha declarados (0,4%), Rio Verde 100%.
- 99 testes passando (21 novos do CAR, com resposta WFS real gravada e shapefile gerado no teste).
- O resumo territorial (área, municípios atingidos, `id_geometria`) e a confirmação já servem a 002 para desenho e arquivo genérico.

## Spec 004 calendário ZARC (15/11, 01h, LK + Claude Code)
- `tellus.zarc`: cliente SISZARC sem login (8 combos, um XLS por UF × cultura × portaria × grupo, solo vazio = todos), regras puras de decêndio e janela, `calendario`, `consultar_data`, `permitido` e rotas `/api/zarc/{culturas,calendario,consulta}`.
- Códigos SISZARC 2026/27: milho 2ª safra 12015080000021; sorgo granífero 2ª 12016740174021; milho 2ª + braquiária 12015080000821; soja 12016720000011.
- Defeito do relatório oficial: a coluna do decêndio 35 vem rotulada "Dev 35". A leitura é por posição, com os rótulos conferidos.
- Grafias diferentes entre SISZARC e IBGE: "Santo Antônio do Leverger" contra "de Leverger" (MT), tratado em `APELIDOS` no script.
- GO: portarias 322 (milho, 30/07/2026), 273 (sorgo, 22/07), 337 (milho + braquiária, 06/08) e 198 (soja, 03/07). 246 municípios. Rio Verde confere com os valores de 14/11 e com o XLS. MT: 142 municípios; MS: 79.
- Download lento (cerca de 4 min por cultura × UF). As outras UFs produtoras seguem em background.
- Portarias ZARC (texto) com parâmetros oficiais para a 005:
  - Milho 2ª (Port. 322): Ze 60 cm; AD1 a AD6 = 24/31,8/41,4/54,6/72,6/95,4 mm; fases G I 20/30/30/20, G II 20/40/40/20, G III 20/50/50/20; ISNA 0,70 (fase I) e 0,55 (fase III).
  - Sorgo (Port. 273): solos tipo 1/2/3 = arenoso/médio/argiloso com CAD 35/55/75 mm; Ze 50 cm; ISNA 0,6 e 0,45.
  - Soja (Port. 198): CAD 24/32/42/55/72/95 mm; Ze 60 cm.
  - Faixas AD em mm/cm (IN SPA/MAPA nº 1/2022, citada na Port. 198): AD1 0,34–0,46; AD2 0,46–0,61; AD3 0,61–0,80; AD4 0,80–1,06; AD5 1,06–1,40; AD6 1,40–1,84.

## Spec 005 base de solo e culturas (15/11, 01h20, LK + Claude Code)
- D-003 respondida: a IN SPA/MAPA nº 1/2022 (com a IN nº 2/2022) traz as classes AD1 a AD6 em mm/cm (Art. 2º) e a equação de pedotransferência pela granulometria de 0 a 40 cm (Art. 3º). A CAD em mm por classe vem da portaria de cada cultura e UF.
- `referencias/culturas/parametros.json`:
  - com fonte (Port. 322 e 273 de GO): Ze, CAD, fases do milho e ISNA;
  - hipótese: Kc e Ky (FAO-56/33 só como método), fases do sorgo e toda a braquiária.
  - Fora de GO, os parâmetros da portaria viram hipótese ("fora da validade regional").
- `tellus.culturas`: `solo.py` (equação e classes, puro), `servico.py` (parâmetros, premissas com edição validada e antes/depois, classificação de solo com passos e status) e rotas `/api/culturas*` e `/api/solo/classificar`.
- A equação oficial não é monotônica na argila (60/15/25 → 0,909; 30/15/55 → 1,043; 15/15/70 → 0,940). Por isso a textura sozinha só dá hipótese.
- 158 testes passando.
- ZARC multi-UF: MG tinha duas grafias diferentes do IBGE ("Barão de/do Monte Alto", "São Thomé/Tomé das Letras"); apelidos acrescentados. MG será refeito com os XLS já baixados.

## Spec 006 motor hídrico (15/11, 02h, LK + Claude Code)
- `tellus.motor`, puro: `eto` (Penman-Monteith FAO-56; Ex. 18 reproduzido com Rn 13,28 e ETo 3,9), `balanco` (FAO-56 cap. 8, Kc único, Ks eq. 84, drenagem, entressafra; perda FAO-33 multiplicativa; falha severa pelo ISNA da portaria) e `simulacao` (mesma data em cada ano; dia ausente exclui o ano).
- `servico`: junta 003 (clima + ETo com altitude da célula POWER), 004 (bloqueio fora da janela, portaria na resposta) e 005 (premissas e solo). Entradas com hash e `versao_entradas`. Rotas `/api/motor/simular` e `/api/motor/janela`.
- D-004: estado inicial com 100% da CAD, pousio Kc 0,30 e palhada 0,15, intervalo de 3 dias. Tudo hipótese editável (`referencias/motor/premissas.json`).
- Rio Verde, grupo I, colheita em 01/01:
  - milho AD4: risco histórico 0% (jan), 8% (01/02), 28% (11/02; o ZARC marca 40%);
  - sorgo tipo 3: 0% até 11/02, 8% (21/02), 20% (01/03), 28% (11/03), 32% (21/03; o ZARC marca 30%).
  - O sorgo aguenta cerca de um mês a mais, como no ZARC.
- 174 testes passando.
- ZARC multi-UF: BA (417 municípios) e PR prontos. TO tinha uma grafia diferente ("Couto de Magalhães" contra "Couto Magalhães"); apelido acrescentado; MG e TO serão refeitos com os XLS em cache.

## Spec 007 economia (15/11, 02h40, LK + Claude Code)
- `tellus.economia`:
  - `conab.py` lê a aba da praça (itens por seção, totais A a J, mês, sistema, produtividade ex-ante) e confere a recomposição. As 65 abas de 2025/26 dão zero divergência. Três abas da Conab omitem "kg/" na produtividade; a unidade é assumida com aviso.
  - `servico.py` calcula a margem nos 3 cenários.
- Preço (D-005): Indicador CEPEA do milho ESALQ/BM&FBovespa (Campinas-SP, R$/sc 60 kg, à vista), último valor em 13/11/2026 de R$ 67,34. O XLS do CEPEA tem a tabela OLE inconsistente; é lido com `ignore_workbook_corruption`. Não há indicador CEPEA de sorgo. O portal de preços da Conab tem certificado inválido. Sorgo fica indisponível e editável. Cobertura tem receita zero e custo informado.
- Cenários (D-006, provisória): perda P75/P50/P25 = conservador/central/favorável; editável; a confirmação fica com a 008.
- Rio Verde, milho, custo operacional de R$ 5.889,09/ha: o empate com R$ 67,34/sc fica em cerca de 87,5 sc/ha.
- 188 testes passando.
- ZARC multi-UF: MA (217) e PI (224) prontos. SP tem erro de codificação no próprio SISZARC ("Santa Cruz da Conceic?o"); apelido acrescentado.
- ZARC multi-UF concluído (15/11, 02h50): GO 246, MT 142, MS 79, MG 853, PR 399, BA 417 (6 conjuntos: sem algumas culturas), TO 139, MA 217, PI 224, SP 645, DF 1 = 3.362 municípios. As contagens conferem com o IBGE. Grafias corrigidas por apelido: MT (Leverger), MG (Monte Alto, Tomé das Letras), TO (Couto Magalhães), SP (Conceição gravado como "Conceic?o" pelo SISZARC). Os XLS brutos ficam em data/raw/zarc/siszarc/ (só os .meta.json no Git).
## Specs 009 vegetação e 010 umidade SMAP (15/11, Frentes A e B + Claude Code, integradas pelo Maestro)
- 009: `tellus.vegetacao` + `/api/vegetacao/contexto` (GET ponto, POST geometria confirmada). MOD13Q1 v061 NDVI como contexto histórico, com proveniência, escala e limitação em cada observação e indicador. Nuvem e QA ruim viram lacuna com motivo. O HLS v2.0 é opcional (indisponível sem credencial, sem bloquear). A série real de Rio Verde está em `referencias/vegetacao/` para a demo offline.
- D-007: a proposta foi testada com dado real (ORNL, sem login): 23 composições, 21 válidas → sustenta como hipótese. HLS: 42 datas L30 e 146 S30 no CMR em 12 meses; o pixel não foi testado (login + COG).
- 010: `tellus.umidade` + `/api/umidade/{produtos,contexto}`. Grade EASE-Grid 2.0 pura, cliente CMR + OPeNDAP, cache por célula. Todo valor é `contexto_regional` com aviso de escala. Célula sem dado fica indisponível, sem vizinho. Nenhum módulo de cálculo importa `umidade` (teste AST).
- D-008: a proposta SPL3SMP_E/30 dias foi testada com dado real (Earthdata, autorizado pelo usuário): 27/30 dias com grânulo, 17 válidas em 12 dias, 0,19 a 0,36 m³/m³ → sustenta como hipótese. A série real está em `referencias/umidade/rio_verde_go/` (demo offline). O cliente agora endereça o OPeNDAP pelo GranuleUR do CMR (o nome .h5 dava 404).
- Integração: routers registrados no `app.py`. 246 testes passando e 1 pulado.
- Pendências: comparação com e sem SMAP depende da 008 (#95). Formato de erro difere entre módulos (`origem`/`campo`) até o contrato da 011. `httpx` está só no grupo dev, mas é usado em runtime por `clima.imerg`, `vegetacao` e `umidade`.
## Spec 011 contrato da API e D-009 (15/11, Frente B + Claude Code, integrada pelo Maestro)
- `tellus.contrato`, versão 1.0.0 (semver: aceita o mesmo MAIOR, com MENOR ≤ ao do servidor). Rotas `/api/contrato/{versao,esquema,pedido/validar}`: só validam, sem executar cálculo.
- A resposta embala a saída real da 006 (`risco_hidrico`) e da 007 (`economia`) por cultura. A 008 é uma seção pendente, sem campos inventados.
- Todo número tem proveniência com os 6 campos da constituição: o teste percorre mais de 1.000 números do caso Rio Verde com 0 falhas.
- Os contextos 009/010 são opcionais. Teste de integração com as séries REAIS de MODIS e SMAP: o `hash_principal` e as culturas não mudam.
- Envelope único de erro `{"erro": {codigo, mensagem, origem, campo}}` em todos os handlers do `app.py` e em `/api/umidade`.
- D-009 (hipótese): 20 MB, 10.000 vértices, 100.000 ha e 60 s, num único arquivo (`contrato/limites.json`). CAR (5.000 por anel e 20 MB) e vegetação passam a ler dali, sem mudar valores.
- Pior caso medido da validação de polígono (O(n²)): 10,2 s com 5.000 vértices; 21,9 s com 10.000; 43,8 s com 20.000. Medir de novo no servidor da demo.
## Spec 002 entrega 2: área por desenho e arquivo (15/11, Frente B + Claude Code, integrada pelo Maestro)
- Módulo `tellus.lavoura`: KML (`xml.etree`, DOCTYPE/ENTITY recusados), KMZ (`zipfile`, tamanho descompactado limitado), GeoJSON (`json`, crs não geográfico recusado) e Shapefile .zip (`pyshp`, que já existia). Rotas `/api/lavoura/{arquivo,desenho,limites}`.
- Desenho no mapa em Leaflet puro (clique = vértice; desfazer, fechar e limpar), sem plugin. Testado manualmente pelo usuário em 15/11.
- Todos os modos de área usam a validação, o resumo (área ha, municípios, `id_geometria` igual entre formatos) e a confirmação do CAR. Limites da D-009 do arquivo único.
- Uma lavoura por arquivo. Erros nomeados: formato_nao_aceito, arquivo_invalido, projecao_nao_suportada, sem_geometria, varias_lavouras, geometria_invalida, vertices_excedidos, area_excedida e arquivo_grande (413). Nunca simplifica.
- 419 testes passando.

## Spec 008 recomendação (15/11, 03h20, LK + Claude Code)
- `tellus.recomendacao`: `avaliar_cultura` (grupos do ZARC; decêndios da janela; `motor.simular` + `economia.margem` por decêndio), `ordenar` (critério público) e `recomendar` (cultura_escolhida | calculo_completo). O cálculo completo é a mesma avaliação juntada, então a paridade vale por construção (e é testada). `POST /api/recomendacao`.
- D-006 confirmada: quartis da perda (conservador P75, central P50, favorável P25), editável.
- Ordem: maior margem conservadora, depois menor risco histórico, depois menor risco ZARC, depois plantio mais cedo.
- Exemplo em Rio Verde (argilosa, colheita em 20/01, sorgo a R$ 50/sc e braquiária a R$ 400/ha informados): 32 alternativas, 7 indisponíveis. A braquiária lidera pelo critério conservador (−400) contra o milho (−925 conservador, +224 central, +749 favorável).
- 198 testes passando; o cálculo completo leva cerca de 1 s.
## #35 chuva ponderada por área (15/11, A1 - Maestro #2 + Claude Code, integrada pelo Maestro)
- A geometria confirmada (`id_geometria` da 002/CAR) é cruzada com as células IMERG de 0,1° (amostragem de 0,005°). A chuva diária é a média ponderada pela fração de área.
- Uma célula sem valor deixa o dia indisponível, com aviso, sem renormalizar nem zerar. A resposta lista cada célula com peso (soma 1), limites, origem, data e qualidade, e o período em UTC.
- Rotas `POST /api/clima/serie` e `/resumo`. O ponto não muda, e a proveniência do ponto ficou idêntica (exemplo gravado da 011 preservado).
- O motor (006) repassa a geometria ao clima (mudança mínima, +6/−4 linhas, autorizada pelo usuário). Os testes antigos do motor passam sem alteração.
- O caso com várias células está provado só com cache SINTÉTICO (caso à mão 0,7 × 3,5 + 0,3 × 20 = 8,45 mm). Por decisão do usuário, as células IMERG vizinhas não foram baixadas. Só a célula da A025 (−17,75; −50,95) tem série real versionada.

## ZARC nacional e #54: 008 no contrato 1.1.0 (15/11, 04h20, LK + Claude Code)
- ZARC 2026/27 das 27 UFs: 5.569 de 5.571 municípios com ao menos uma cultura zoneada. O milho 2ª safra não existe no SISZARC em AL, AM, AP, CE, PB, PE, RN, RS, SC e SE; nesses casos o app declara "sem ZARC publicado". Grafias SISZARC × IBGE resolvidas por apelido: PE (Lagoa de Itaenga), RJ (Paraty), RN (Arez; Boa Saúde = Januário Cicco), RR (São Luiz do Anauá), SE (Amparo do São Francisco, Graccho Cardoso).
- #54, contrato 1.1.0 (MENOR, aceita 1.0.x):
  - a seção `recomendacao` usa a 008 real; `comparar_alternativas` é traduzido para `calculo_completo`;
  - o grupo `nao_sei` vai para a 008, e as seções por cultura viram não obrigatórias;
  - falha da 008 vira erro da seção, sem derrubar as outras;
  - rota `POST /api/contrato/calcular`.
- Cotação informada (pedido do Pedro): `origem_informada` e `data_informada` nas premissas editadas, juntos. Chegam a `alteracoes` e `premissas.preco.informado` na 007 (o sorgo passa a `informado_pelo_produtor`), viram proveniência `informado_*` na seção da economia e na da 008, e entram nas hipóteses da alternativa. Implementado direto a partir dos tipos da `012-interface-web` (a branch de backend do recado não foi publicada).
- Isolamento do SMAP mantido: o contrato não importa umidade nem vegetação. O `app.py` pluga os provedores de contexto (`contrato.PROVEDORES_CONTEXTO`).
- 451 testes passando.

## Spec 013 identidade visual, parte 1 (15/11, 04h20, LK + Claude Code)
- D-011: o LK escolheu a paleta "Safra" e o tom técnico e direto, entre três paletas com contraste AA calculado.
- `frontend/src/styles/marca.css` (tokens do Tailwind 4 e `.tellus-selo`), `frontend/src/components/marca/Selo.astro` (texto + ícone próprio, nunca só cor) e `docs/marca/GUIA_DE_MARCA.md` (uso, tom com palavras proibidas, inventário de licenças).
- Contraste: 20 de 20 pares ≥ 4,5:1 (`scripts/verificar_contraste.py`, também em `backend/tests/marca`).
- O favicon padrão do Astro (elemento de terceiros) foi trocado pelo ícone TELLUS da equipe.
- Pendências humanas: arquivo LICENSE do repositório e busca de marca no INPI.
- Falta aplicar nas telas (#59, #107), que depende da 012 do Pedro na `main`.

## 012 integrada com o contrato real e 013 completa (15/11, 05h10, LK + Claude Code)
- A branch `012-interface-web` do Pedro foi mergeada sem conflito (152 testes vitest, 8 páginas). Não havia PR; as telas usavam só dados de exemplo.
- Troca do adaptador:
  - a tela inicial grava a lavoura escolhida ou confirmada (`lavoura.ts`, ponto ou geometria);
  - as Entradas oferecem "Usar a lavoura confirmada";
  - `contrato.ts` monta o pedido 1.1.0, chama `POST /api/contrato/calcular` e converte para os tipos da 012;
  - o resultado mostra as alternativas reais (sem o selo "DADO DE EXEMPLO") ou cai no exemplo identificado.
  - Ao vivo: HTTP 200 em 0,85 s, estado final, 26 alternativas, contextos 009/010 disponíveis.
- 013 parte 2: marca no layout e nos selos de proveniência e erro. Verificação #107 nas 8 telas: rótulos Fonte/Hipótese/Aviso/Erro presentes e nenhum "previsão".
- Testes: 461 backend + 158 frontend.
- Issues fechadas: #57, #100, #101, #59, #107, #58. Abertas com comentário: #102 (só o preço do sorgo chega ao backend; premissas do milho no editor ainda são de exemplo) e #103 (indicador de etapas ainda do exemplo). Continuam com humanos: #104 (teste com 5 pessoas), #72 (D-010), #56.

## #102, #103, #53/#95, D-010, #51 e #110 (15/11, 05h–06h30, LK + Claude Code)
- #102: as premissas editadas (preço, custo e produtividade do milho; CAD; cotação do sorgo) vão ao cálculo real, e o resultado mostra padrão → novo valor. Bug corrigido: CAD digitada sem classe ZARC (sorgo usa tipo de solo) derrubava a recomendação inteira; agora só a cultura afetada fica indisponível.
- #103: resultado real com etapa atual durante o cálculo, `estado_geral` do backend (incompleto e erro aparecem como PARCIAL), lista de fontes com data da cópia guardada e erros com origem, cache e ação.
- #53/#95: teste com a recomendação real e a série SMAP real, com e sem umidade: resultado principal idêntico. #52 fechada.
- D-010 (#72): computador e celular, sem login, servidor local. Telas conferidas em 390 px; o menu de etapas passou a quebrar linha. LICENSE MIT na raiz; busca no INPI dispensada.
- #51: o contexto de vegetação mostra MODIS (23 composições em Rio Verde) e HLS separados; HLS indisponível sem credencial, com o motivo, sem bloquear o fluxo.
- #110:
  - IMERG com 2 células reais: célula vizinha `-17.85_-50.95` (2025-01-01 a 2025-09-30, 273 dias) versionada em `referencias/clima/rio_verde_go_sul/` (`scripts/exportar_imerg_celula.py`). Teste: retângulo que cruza -17,8°, pesos 0,5/0,5 somando 1, e a média de cada dia confere com a conta independente.
  - Validação INMET fora da A025: arquivos anuais do portal (`scripts/preparar_inmet_validacao.py`, mesmo método da pesquisa; conferido contra a série da A025 de 2025: 357 dias, 0 divergências). A016 Jataí está em pane no catálogo e foi descartada; usada a A026 Mineiros-GO (operante, 170 de 731 dias completos em 2024–2025, todos em 2024). Jan–jun/2024, 103 dias pareados: IMERG −21,7% de viés, MAE 1,74 mm/dia; POWER −48,6% (só comparação). Série em `referencias/clima_inmet/A026/`, IMERG da célula em `referencias/clima/mineiros_go/`. Sem POWER guardado, a validação mostra só o IMERG e avisa.
- Testes: 469 backend + 168 frontend.
