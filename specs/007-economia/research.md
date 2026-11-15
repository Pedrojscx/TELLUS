# Research: 007-economia

Testes feitos em 2026-11-15, por volta de 02h20 BRT.

## R1. Planilhas de custo da Conab

Exemplo: aba "Rio Verde-GO-2026" do milho 2ª safra.
- **Cabeçalho**: "AGRICULTURA EMPRESARIAL - MILHO - PLANTIO DIRETO…", "Mês/Ano: Março/2026" e
  "Produtividade Média: 6000,00 kg/ha | Ex-Ante".
- **Itens numerados** em seções: I custeio (A), II outras despesas (B), III financeiras (C),
  IV depreciações (E), V outros custos fixos (F) e VI renda de fatores.
- **Totais**: custo variável (D = A+B+C), custo fixo (G = E+F), custo operacional (H = D+G) e
  custo total (J = H + renda).
- **Recomposição**: as 65 abas de 2025/26 (soja 32, milho 2ª 27, sorgo 6) recompõem todos os
  totais a partir dos itens, com tolerância de R$ 0,10 e zero divergência.
- **Defeito da Conab**: 3 abas (Cascavel-PR-2026 milho, São Gabriel-RS-2025/2026 soja) escrevem
  "6000,00 ha", sem "kg/". A unidade é assumida com aviso.
- **Rio Verde-GO 2026 (março/2026, plantio direto)**:
  - milho 2ª: custo operacional 5.889,09, total 6.886,16, 6.000 kg/ha;
  - sorgo: operacional 3.806,76, total 4.788,11, 3.600 kg/ha;
  - os valores conferem com o registro da equipe.

## R2. Preços (D-005)

- **CEPEA**: indicadores publicados em cepea.org.br/br/indicador: açúcar, algodão, arroz,
  bezerro, boi gordo, café, citros, etanol, feijão, frango, leite, mandioca, **milho**, ovinos,
  ovos, soja, suíno, tilápia e trigo. **Não há sorgo.**
- **Milho**: "INDICADOR DO MILHO ESALQ/BM&FBOVESPA", série diária em
  `cepea.org.br/br/indicador/series/milho.aspx?id=77` (XLS com 5.555 linhas desde 02/08/2004;
  colunas Data, À vista R$ e À vista US$). Último valor: 13/11/2026, R$ 67,34/sc 60 kg. A região
  de referência é Campinas-SP, sem frete até a fazenda.
- **Conab, preços agropecuários** (`portaldeinformacoes.conab.gov.br`, `consultaweb.conab.gov.br`):
  o certificado TLS não confere com o nome do servidor. Desligar a verificação seria inseguro;
  rejeitado.
- **Decisão**: milho pelo CEPEA (o último dia disponível, com data); sorgo indisponível e editável;
  cobertura com receita zero.

## R3. Nível de custo e cenários

- O nível padrão é o custo operacional (inclui depreciação e arrendamento, exclui a renda de
  fatores próprios), como no prompt da etapa 1. O produtor pode trocar para custeio, custo variável
  ou custo total.
- D-006 (provisória): cenários pela perda simulada. Conservador = P75 da perda; central = P50;
  favorável = P25. Editável. Confirmação na 008.

## R4. Exemplo de margem (Rio Verde, milho, perdas de teste P25/P50/P75 = 10/20/40%)

Conservador −1.848,69; central −501,89; favorável +171,51 R$/ha. O empate com R$ 67,34/sc e custo
operacional de 5.889,09 fica em cerca de 87,5 sc/ha.
