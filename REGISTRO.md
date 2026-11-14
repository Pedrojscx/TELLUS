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
