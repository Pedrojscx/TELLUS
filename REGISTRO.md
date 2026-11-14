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
- (aberta) Ideia e região.
