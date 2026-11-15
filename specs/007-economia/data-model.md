# Data Model: 007-economia

## Pedido (`POST /api/economia/margem`)

`{lat, lon, cultura, perda_relativa_quantis? | simulacao? (pedido da 006), edicoes?, percentis?}`

As edições aceitas são:
- `preco_r_saca` (0 a 1000);
- `produtividade_kg_ha` (0 a 30000);
- `nivel_custo` (`custeio` | `custo_variavel` | `custo_operacional` | `custo_total`);
- `custo_item.<código>` (≥ 0);
- `custo_r_ha`, que substitui o total (0 a 100000).

Os percentis são `{conservador, central, favoravel}`, cada um com valor 10, 25, 50, 75 ou 90.

## Resposta

| Campo | Conteúdo |
|---|---|
| margem_disponivel / motivos_indisponivel | False quando falta preço, custo ou simulação. Nunca margem factual com dado ausente |
| estado | `fonte` ou `com_premissas_do_produtor` |
| cenarios.{conservador,central,favoravel} | percentil_perda, perda_relativa, produtividade_kg_ha, sacas_ha, receita_r_ha, custo_r_ha e margem_r_ha |
| custo_conab | praça, código IBGE, distancia_km, planilha, mes_referencia, sistema, unidade, nivel, itens[] {codigo, nome, grupo, valor_r_ha, valor_usado_r_ha, editado}, total_nivel_r_ha, totais_planilha, avisos_planilha e fonte (arquivo, url, data, sha256) |
| premissas | preco (status `fonte`, `indisponivel` ou `nao_se_aplica`, com fonte e motivo), produtividade, custo e percentis (hipótese) |
| alteracoes[] | premissa, valor_anterior, valor_novo, unidade, origem_novo |
| comparacao | margem_anterior_r_ha e margem_nova_r_ha por cenário |
| versao_premissas | hash das premissas, itens e perdas |
| versao_entradas_motor | versão das entradas da 006, quando a simulação foi feita aqui |
