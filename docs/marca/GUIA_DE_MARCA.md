# Guia de marca do TELLUS

Spec 013 (identidade visual). Decisão D-011 de 15/11/2026: paleta **Safra** e tom **técnico e
direto**, escolhidos pelo LK. Responsáveis: LK e Pedro. Versão 1.0, de 15/11/2026.

Princípio que manda em tudo: a identidade **nunca esconde** fonte, hipótese, aviso ou erro, e nunca
faz frequência histórica parecer previsão (constituição: rastreabilidade e respeito à escala).

## 1. Nome

- **TELLUS**, em maiúsculas na marca, e "TELLUS" ou "Tellus" no texto corrido.
- Por extenso: *Terrestrial Environmental Learning & Land Utilization System*.
- Linha de apoio: "Milho, sorgo ou cobertura depois da soja: risco e margem com dados NASA e fontes oficiais."
- O nome não foi pesquisado em base de marcas (INPI). A equipe dispensou a busca porque é um projeto
  de hackathon; fazê-la antes de qualquer uso além disso.

## 2. Ícone

`docs/marca/tellus-icone.svg` (igual a `frontend/public/favicon.svg`): quadrado verde-folha, três
faixas de lavoura em marfim e um ponto dourado de satélite.
- Usar sobre fundo claro ou escuro, sem distorcer, girar, trocar as cores ou pôr sombra.
- Tamanho mínimo: 16 px (favicon) e 32 px nas telas.
- Criação da equipe TELLUS, sem elemento de terceiros. Substitui o `favicon.svg` padrão do Astro,
  que era um elemento de terceiros e foi removido junto com o `favicon.ico`.

## 3. Cores (paleta Safra)

Definidas em `frontend/src/styles/marca.css` como tokens do Tailwind 4 (`bg-tellus-primaria`,
`text-tellus-hipotese` etc.). Contraste conferido por `python scripts/verificar_contraste.py`: em
15/11, os **20 pares passaram** do mínimo AA de 4,5:1.

| Papel | Cor | Contraste sobre o fundo |
|---|---|---|
| Fundo | `#FFFDF7` marfim | — |
| Superfície (cartões) | `#FFFFFF` | — |
| Texto | `#1A1A1A` | 17,1:1 |
| Texto secundário | `#57534E` | 7,5:1 |
| Primária (ações, marca) | `#2F6B2F` verde-folha | 6,3:1 (branco sobre ela: 6,4:1) |
| Destaque | `#7A5C00` dourado escuro | 6,2:1 |
| Fonte (proveniência) | `#155E75` azul-petróleo | 7,1:1 |
| Hipótese | `#7A5C00` dourado | 6,2:1 (sobre o fundo do selo: 5,6:1) |
| Aviso | `#9A3412` laranja-escuro | 7,2:1 (selo: 6,3:1) |
| Erro | `#B91C1C` vermelho | 6,4:1 (selo: 5,5:1) |

O dourado claro `#E0B84A` aparece **só** no ponto decorativo do ícone, nunca em texto.

## 4. Estados críticos: nunca só cor (#106)

Use sempre o componente `frontend/src/components/marca/Selo.astro`. Cada estado tem **texto +
ícone + traço**, e por isso continua legível em monocromia, impressão ou daltonismo:

| Estado | Texto obrigatório | Ícone | Traço à esquerda |
|---|---|---|---|
| Fonte | "Fonte: …" | círculo com "i" | contínuo |
| Hipótese | "Hipótese: …" | triângulo tracejado | **tracejado** |
| Aviso | "Aviso: …" | triângulo com "!" | contínuo |
| Erro | "Erro: …" (com `role="alert"`) | círculo com "×" | contínuo e mais grosso |

Regras:
- Hipótese e hipótese editada pelo produtor mostram o selo ao lado do valor, sempre.
- Erro nunca aparece só como borda vermelha: o selo com texto vem junto.
- Cor de semáforo (verde = bom, vermelho = ruim) não pode ser o único sinal de risco. O número e o
  rótulo ("risco histórico 8%") vêm sempre escritos.

## 5. Tom de texto: técnico e direto

- Frases curtas, número com unidade, sem jargão desnecessário.
- Exemplos:
  - "Risco histórico de falha severa: 8% (2 em 25 anos). Não é previsão."
  - "Margem no cenário conservador: −R$ 925/ha."
  - "Preço informado pelo produtor: Cooperativa X, 14/11/2026."
  - "Sem ZARC publicado para sorgo neste município."
- **Proibido** para número derivado de série histórica (FR-004): "previsão", "vai chover", "vai
  faltar água", "garantido". Use "frequência histórica", "em X de Y anos" e "risco histórico".
- Risco ZARC (oficial) e risco histórico (TELLUS) sempre com o nome completo, nunca só "risco".
- Fonte com nome, data e unidade ("IMERG Final V07B, 2001–2025, mm/dia").

## 6. Tipografia

- Pilha de fontes do sistema (`--font-tellus`): system-ui, Segoe UI, Roboto, Helvetica, Arial, Noto
  Sans. Funciona offline e não exige licença de fonte de terceiros.
- Números de resultado com algarismos tabulares (`.tellus-numero`) para alinhar colunas.

## 7. Inventário de elementos e licenças (#105, SC-002)

| Elemento | Origem | Licença | Data | Responsável |
|---|---|---|---|---|
| Nome TELLUS | equipe | da equipe (busca de marca pendente) | 14/11/2026 | equipe |
| Ícone `tellus-icone.svg` / `favicon.svg` | criado pela equipe | da equipe | 15/11/2026 | LK |
| Ícones dos selos (SVG inline em `Selo.astro`) | criados pela equipe | da equipe | 15/11/2026 | LK |
| Paleta e tokens (`marca.css`) | criados pela equipe | da equipe | 15/11/2026 | LK |
| Fontes | do sistema operacional do usuário | não distribuídas pelo TELLUS | — | — |
| Tailwind CSS (ferramenta) | terceiros | MIT | já no projeto | — |
| Leaflet (mapa) | terceiros | BSD-2-Clause | já no projeto | — |
| Tiles do mapa | OpenStreetMap | ODbL, atribuição "© OpenStreetMap" obrigatória (já exibida no mapa) | — | — |

**Elementos de terceiros incorporados à identidade: nenhum.** Nenhum elemento com licença indefinida
entrou.

**Licença:** o repositório inteiro (código, ícone e textos) está sob a licença MIT, no arquivo `LICENSE`
da raiz (decisão da equipe, 15/11).

## 8. Aplicação nas telas (#59, #107)

A spec manda aplicar a identidade só **depois** do fluxo funcional validado (FR-001). A interface
(012) está na branch `012-interface-web`, ainda sem merge.

Quando ela entrar:
1. importar `marca.css` no `global.css`;
2. trocar os selos de estado pelo `Selo.astro`;
3. comparar as telas principais antes e depois (fonte, hipótese, aviso e erro visíveis; nenhum
   texto de previsão);
4. registrar a comparação.
