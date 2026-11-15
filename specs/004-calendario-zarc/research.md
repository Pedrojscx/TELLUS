# Research: 004-calendario-zarc

Testes feitos em 2026-11-15, por volta de 00h20 BRT.

## R1. Sequência do SISZARC (FR-002)

Formulário `gerarRelatorioPublicacoesDoZarc.action`. Cada combo é um POST do formulário
inteiro para `gerarRelatorioPublicacoesDoZarc!<ação>.action`, e a página volta com o próximo
combo preenchido. Não precisa de login.

| Nível | Campo | Ação seguinte | Valor usado |
|---|---|---|---|
| 0 | `form.filtroConsulta.anoSafra` | carregarComboCulturas | `2026 / 2027` |
| 1 | `cultura.codigoCultura` | carregarComboOutrosManejos | ver R2 |
| 2 | `tipoSistemaCultivo.cdTipoCultivo` | carregarComboClima | `1` (Sequeiro) |
| 3 | `tipoClimaCultivo.idTipoClima` | carregarComboUfs | `0` (Não se aplica) |
| 4 | `sgUF` | carregarComboPortarias | UF |
| 5 | `numeroPortaria` | carregarComboGrupos | todas as listadas |
| 6 | `grupo.cdGrupo` | carregarComboSolos | todos os listados (ex.: 20 = GRUPO I) |
| 7 | `solo.cdSolo` | — | vazio = todos os solos |

O XLS vem de `gerarRelatorioXLS.action` com `isRelatorio=true`: cerca de 1,1 MB por UF, uma
linha por município × solo, com as colunas Safra, Cultura, UF, Portaria, Data Portaria,
Município, Grupo, Solo e Dec 1 a Dec 36. O valor é o risco em %; 0 quer dizer fora da janela.

**Defeito do relatório oficial**: a coluna do decêndio 35 tem o rótulo "Dev 35". Por isso a
leitura é por posição (36 colunas a partir de "Dec 1"), e o rótulo de cada uma é conferido
(`De[cv] n`).

## R2. Códigos de cultura (safra 2026/2027)

| Chave | Código SISZARC | Nome |
|---|---|---|
| milho_2a_safra | 12015080000021 | Milho 2ª Safra |
| sorgo_granifero_2a_safra | 12016740174021 | Sorgo Granífero 2ª Safra |
| milho_2a_safra_braquiaria | 12015080000821 | Milho 2ª Safra consorciado com Braquiária |
| soja | 12016720000011 | Soja |

## R3. Solos

Milho, milho com braquiária e soja usam as classes AD1 a AD6. O sorgo usa os solos "1", "2" e
"3", os tipos de solo do ZARC: arenoso, textura média e argiloso. O padrão de Rio Verde confirma
essa leitura: o tipo 1 tem a janela mais curta e o tipo 3 a mais longa, como registrado em 14/11.

## R4. Goiás (validação)

| Cultura | Portaria | Data | Grupos |
|---|---|---|---|
| Milho 2ª safra | 322 | 30/07/2026 | I, II |
| Sorgo granífero 2ª safra | 273 | 22/07/2026 | I, II, III |
| Milho 2ª safra com braquiária | 337 | 06/08/2026 | I, II |
| Soja | 198 | 03/07/2026 | I, II, III |

Os 246 municípios do relatório foram ligados ao código IBGE pelo nome normalizado + UF, sem
nenhuma falha. Rio Verde confere com o registro da equipe (milho G I/G II e sorgo G I/G II/G III).

## R5. Ligação nome → IBGE

O relatório traz o nome do município, não o código. A ligação usa nome sem acento, em minúsculas
e com pontuação normalizada, mais a UF. O script falha e lista o município se algum ficar sem
código, sem nunca ligar pelo mais parecido.
