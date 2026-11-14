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
