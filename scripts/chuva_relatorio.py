"""Render the research report from the audited CSV outputs."""
from pathlib import Path
import json,datetime
import pandas as pd
R=Path(__file__).resolve().parents[1]; O=R/'data/processed/pesquisa_chuva'; F=R/'docs/pesquisa_chuva'
def read(n):return pd.read_csv(O/(n+'.csv'))
def table(a):
 a=a.copy()
 for c in a:
  if pd.api.types.is_float_dtype(a[c]):a[c]=a[c].map(lambda x:'—' if pd.isna(x) else f'{x:.2f}')
 return '| '+' | '.join(a.columns)+' |\n|'+'|'.join(['---']*len(a.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in a.to_numpy())
m=read('three_source_metrics');mon=read('three_source_monthly');dry=read('three_source_dry_summary');daily=read('daily_all_sources');summary=json.loads((O/'summary.json').read_text());cells=json.loads((O/'cells.json').read_text());ev=read('correction_evaluation');audit=read('hourly_audit'); im=read('imerg_daily')
allm=m[(m.scope=='Jan-Jun')&(m.year=='ALL')]
years=m[(m.scope=='Jan-Jun')&(m.year!='ALL')]
annual=read('annual_seasonal');pair=annual[annual.scope=='Jan-Jun']
audit['valid_hour_percent']=100*(audit.rows-audit.missing_hours-audit.negative_fill_hours)/audit.expected_hours
short=years[['year','source','n','inmet_mm','source_mm','bias_percent','mae_mm_day','rmse_mm_day']]
d=dry[(dry.scope=='Jan-Jun')&(dry.threshold_mm==1)].pivot(index='year',columns='source',values='max_observed_run').reset_index()
meta={'analysis_date':'2026-11-14','station':'INMET A025','station_source':'https://portal.inmet.gov.br/dadoshistoricos','station_version':'annual automatic-station CSV; no version identifier supplied','station_obtained_at':'exact original timestamp unknown; team log reports 2026-11-14','station_years':[2008,2012,2016,2019,2022,2024,2025],'power':{'parameter':'PRECTOTCORR','api_version':'v2.10.3','source':'MERRA2','units':'mm/day','time_standard':'UTC','period':'2008-01-01/2025-12-31','queries':'data/raw/pesquisa_chuva/power_*meta.json'},'imerg':{'product':'GPM_3IMERGDF','version':'07 / granules V07B','collection':'C2723754864-GES_DISC','doi':'10.5067/GPM/IMERGDF/DAY/07','units':'mm/day','period':'January–June of station years; July–September 2025 context','cmr_temporal_extent':'1998-01-01/2025-09-30 (catalog snapshot)','daily_files':len(im),'valid_count_required':48,'daily_queries':'data/raw/pesquisa_chuva/imerg/*.meta.json'},'cells':cells,'thresholds':{'day_hours':24,'month_fraction':.95,'complete_period_fraction':1.,'wet_day_mm':1.},'sources_fetched':'data/raw/pesquisa_chuva/*.meta.json','input_hashes':['inputs.json','imerg_inputs.json']}
(O/'metadata.json').write_text(json.dumps(meta,indent=2))
text=f'''# Chuva para a segunda safra em Rio Verde-GO

Pesquisa executada em 14/11/2026. Escopo: milho, sorgo e cobertura após a soja. Os números abaixo descrevem o passado; não são previsão da próxima safra.

## Recomendação

Use o **INMET A025 como referência local**, apenas em dias completos e após o controle descrito abaixo. Use **IMERG Final V07B como a opção de grade a testar no balanço hídrico**, com a diferença local visível. A comparação diária permite avaliar o IMERG; não se deve preferi-lo apenas por ser NASA ou ter grade menor.

No conjunto de janeiro–junho, o IMERG teve viés de −1,03%, MAE de 4,13 mm/dia e RMSE de 8,59 mm/dia; o POWER teve −26,96%, 4,53 e 9,85 mm/dia. O IMERG foi melhor no conjunto, mas não em todo ano ou critério.

Não use POWER original nem a correção mensal testada como chuva local validada. POWER pode continuar como fonte candidata das demais variáveis climáticas, que esta pesquisa não validou. Não misture chuva UTC com ETo em dias LST sem alinhar os períodos.

A análise climática está pronta. A escolha entre milho e sorgo por déficit, produtividade ou margem **ainda não está demonstrada**: não há modelo agrícola executável neste estado do repositório. A diferença de chuva é grande o bastante para exigir um teste de sensibilidade quando o modelo existir. Não se pode traduzir essa diferença diretamente em perda de produção.

## Dados e escala

| Fonte | Produto e período disponível nesta pesquisa | Unidade e escala |
|---|---|---|
| INMET | A025; 2008, 2012, 2016, 2019, 2022, 2024 e 2025 | mm por hora; ponto em -17,78527777, -50,965; altitude 780,11 m; fundação 17/05/2007 |
| POWER | PRECTOTCORR, API v2.10.3, origem MERRA2 no novo JSON; 2008–2025 UTC | mm/dia; grade nativa 0,5° latitude × 0,625° longitude |
| IMERG | GPM_3IMERGDF Final 07, arquivos V07B; jan–jun nos sete anos; jul–set/2025 como contexto | mm/dia; grade 0,1° × 0,1°; dia UTC |

O arquivo local antigo do POWER cobre 1984–10/11/2026 em LST. Foi preservado. O INMET local cobre sete anos isolados; isto **não é uma normal climatológica contínua**. Não baixamos de novo os CSV locais. A data exata da obtenção original dos CSV não veio com os arquivos; o registro informa 14/11/2026. Os hashes fixam a versão usada.

O CMR oficial lista a coleção diária IMERG desde **01/01/1998 até 30/09/2025** no retrato consultado. O resumo do próprio catálogo ainda diz “beginning 2000”; guardamos ambos e usamos apenas os anos efetivamente obtidos. Não se inferiu cobertura de 2026. Outubro–dezembro/2025 retornaram 404 nas tentativas; a análise não preenche esse intervalo.

### Células

A célula IMERG tem centro **-17,75, -50,95**, índices zero-based longitude 1290 e latitude 722; distância de **{cells['imerg']['distance_km']:.2f} km** à estação. O NetCDF confirma os eixos e coordenadas. Aproximadamente 11 × 11 km; esta média espacial não equivale a um pluviômetro.

O ponto antigo POWER (-17,80, -50,92) fica a **{cells['original_query_distance_km']:.2f} km** da estação, mas cai do outro lado de uma borda de célula. Seus valores de janeiro/2025 são idênticos aos do centro **-18, -50,625**, a {cells['power_original_point_cell']['distance_km']:.2f} km da estação. Ao consultar a coordenada exata da A025, os 31 valores são idênticos aos do centro **-18, -51,25**, a {cells['power_station_cell']['distance_km']:.2f} km. A grade é de cerca de 56 × 66 km neste local. A identificação usa a grade nativa e esse teste de igualdade; o JSON POWER não devolve um ID explícito de célula.

A comparação principal usa POWER na estação. `original_point_comparison.csv` mantém a análise do ponto antigo para auditar o registro.

## Método e controle de qualidade

1. Ler o INMET em Latin-1, com vírgula decimal e dois formatos de data/hora. Rejeitar chuva negativa e códigos de preenchimento; manter ausências como ausências. Não houve hora duplicada. Não houve registro acima de 100 mm/h; isso é apenas uma triagem, não prova de calibração.
2. O [glossário INMET](https://portal.inmet.gov.br/glossario/tempo) define precipitação automática como o total da última hora antes da mensagem. Para o dia UTC D, somar os registros de **01:00 de D até 00:00 de D+1**. Só aceitar **24 horas válidas**. A falta do arquivo do ano seguinte impede fechar alguns dias 31/12; não substituímos essas horas por zero.
3. O POWER antigo usa LST, definido em faixas de longitude de 15°. Baixamos PRECTOTCORR em UTC para evitar misturar dias. `mm/day` em uma janela de um dia corresponde ao acumulado em mm; não multiplicar por 24 novamente.
4. O IMERG diário V07 fornece a média das taxas válidas × 24. Ler `precipitation`, não confundir com `MWprecipitation`. Exigir **precipitation_cnt=48**. Em dados de meia hora, a conversão seria soma de taxa em mm/h × 0,5 h. Ler preenchimento pela máscara NetCDF. Todos os {len(im)} arquivos obtidos tiveram contagem 48 na célula. Guardamos `randomError` em mm/dia, sem tratá-lo como intervalo de confiança ou erro medido contra a estação.
5. Comparar somente datas válidas comuns. A comparação de três fontes usa a mesma máscara para INMET, IMERG e POWER. Nenhum total mensal do arquivo antigo foi usado para inferir dias secos.
6. Aceitar meses com pelo menos **95% dos dias pareados** para erros de volume mensal e ajuste. É um limite explícito de até 5% de dias ausentes, não uma garantia de que a chuva perdida é pequena. Mesmo nesses meses, a soma recebe o rótulo **acumulado nas datas pareadas**. Só chamar de total completo com **100% dos dias**. Para ano/temporada, usar 95% como triagem descritiva e 100% para total completo ou entrada diária sem preenchimento no modelo.
7. Dia chuvoso: **≥1 mm**; seco: **<1 mm**. Ausências interrompem as sequências. Uma sequência junto a uma falha ou borda é censurada: o comprimento observado é um limite inferior. Guardamos também o máximo entre sequências inteiras e testamos limiares 0,1 e 5 mm. Estes limiares não são medidas de estresse da cultura.

### Cobertura

{table(audit[['year','rows','missing_hours','negative_fill_hours','duplicate_hours','valid_hour_percent']])}

INMET × POWER: {summary['n_days']} dias esperados, **{summary['all']['n']} pareados e {summary['excluded_days']} excluídos**. Janeiro–junho: 1.271 esperados, **{summary['jan_jun']['n']} válidos e {1271-summary['jan_jun']['n']} excluídos**. Há {summary['accepted_months_95pct']} meses com cobertura ≥95%, dos quais {summary['complete_months']} completos, em 84 meses examinados. O POWER não teve dias ausentes neste recorte.

Nenhum ano INMET ficou 100% completo após o fechamento UTC. Janeiro–junho/2019 é o único semestre completo. Os outros acumulados abaixo são **parciais pareados**, não totais anuais ou sazonais completos. Os 14 registros horários ausentes de 2025 mostram por que a cobertura arredondada para “1,00” no registro anterior escondia falhas. Em 2024, faltam 3.367 horas; seus resultados não representam o ano inteiro.

## Resultados medidos

### Janeiro–junho: três fontes nas mesmas datas

Viés = fonte − INMET. Viés percentual = 100 × soma das diferenças / soma INMET. MAE = média do erro absoluto; RMSE = raiz da média do erro ao quadrado. A correlação de Pearson é informação complementar.

{table(allm[['source','n','inmet_mm','source_mm','bias_mm_day','bias_percent','mae_mm_day','rmse_mm_day','correlation','inmet_wet_percent','source_wet_percent']])}

{table(short)}

O viés IMERG agregado próximo de zero esconde compensações: +25,64% em 2012 e −19,50% em 2025. Em 2016, POWER tem MAE e RMSE diários menores que IMERG, embora seu viés de volume seja maior. IMERG indica chuva em 44,50% dos dias, contra 35,14% no INMET; portanto também não reproduz toda a ocorrência local.

A comparação agrega anos de cobertura desigual; não equivale à média de sete anos completos. `three_source_epochs.csv` separa janeiro–fevereiro, março–abril e maio–junho. São épocas do calendário, não fases fenológicas: estas dependem da data de plantio e da cultivar.

### Volumes mensais

Só meses com ≥95% de cobertura, sobre as datas comuns; erros em mm por mês pareado:

{table(read('monthly_aggregate_metrics'))}

### Volumes por semestre com cobertura ≥95%

Cinco semestres passam nesta triagem. Os erros abaixo usam **acumulados pareados por semestre**, não totais completos nem extrapolação dos dias ausentes. Excluem 2012 e 2024 desta síntese; as tabelas por ano ainda mostram esses anos com sua cobertura.

{table(read('seasonal_aggregate_metrics'))}

### Sequências secas

Maior trecho observado em janeiro–junho, com limiar <1 mm/dia. Falhas e limites do semestre podem truncar a sequência; não interpretar como duração exata da maior seca do ano.

{table(d)}

Em 2008, o maior trecho seco observado foi 32 dias no INMET e IMERG, contra 15 no POWER. Em 2025, foi 13, 17 e 14 dias, respectivamente. Esses exemplos mostram que o menor volume do POWER não implica sempre maior sequência seca.

O arquivo `three_source_dry_summary.csv` inclui frequência, contagem, máximos observados e máximos não censurados para os três limiares. As diferenças na ocorrência da chuva permanecem relevantes mesmo quando os totais parecem próximos.

![Acumulados mensais nas mesmas datas](three_sources_monthly.png)

![Viés e sequências secas](three_sources_bias_dry.png)

### Discrepância de 2025

Nos **180 dias pareados de janeiro–junho/2025**, INMET = **969,20 mm**, IMERG = **780,19 mm**, POWER na estação = **392,16 mm**. O ponto antigo POWER soma **426,90 mm** nessas mesmas datas. Assim, a troca de célula não explica a diferença inteira; neste caso a célula da estação fica ainda mais baixa. O dia 21/01 tem apenas 23 horas válidas e foi excluído.

No ano, os **357 dias pareados** somam 1.534,00 mm no INMET, 628,52 mm no POWER da estação e 676,48 mm no ponto antigo. **Não são totais anuais completos.** Não há IMERG de outubro–dezembro/2025 nesta coleção no acesso testado, portanto não calculamos um total anual de três fontes.

O valor antigo de cerca de 1.548 mm para INMET somava horas disponíveis, enquanto o POWER cobria outros intervalos. Essa comparação não tinha máscara diária comum. A nova máscara reduz esse problema, mas mantém grande diferença em 2025. Em 2019, por exemplo, o ponto antigo passa de aparente excesso anual de cerca de 14% no registro para **−6,06% nos dias pareados**; isso ilustra o efeito das falhas.

![Chuva diária em 2025](2025_daily.png)

### Sensibilidade ao fechamento da hora

Teste auxiliar com as mesmas datas válidas nos dois fechamentos: deslocamento 0 soma rótulos 00–23; deslocamento 1 soma as horas encerradas em 01–00, método principal. O teste não escolhe o horário por maior correlação.

{table(read('time_sensitivity')[['inmet_timestamp_shift_hours','n','bias_percent','mae_mm_day','rmse_mm_day','correlation']])}

## Correção mensal do POWER

Teste simples e separado no tempo: fator de cada mês = soma INMET / soma POWER nas datas de ajuste. Ajuste em **2008, 2012, 2016 e 2019**; avaliação em **2022, 2024 e 2025**. Exigir três meses-ano de ajuste com cobertura ≥95%. Não usar os anos de avaliação para ajustar os fatores. Março e julho não passam no critério; seus fatores ficam ausentes, sem substituição por 1 ou por fator anual.

Avaliação sobre a mesma amostra para original e corrigido, só meses elegíveis:

{table(ev[(ev.year=='ALL')][['scope','source','n','bias_percent','mae_mm_day','rmse_mm_day','source_wet_percent']] if 'source_wet_percent' in ev else ev[(ev.year=='ALL')][['scope','source','n','bias_percent','mae_mm_day','rmse_mm_day','power_wet_percent']])}

A correção não resolveu o viés recente nem produziu melhora ampla nos erros diários. O conjunto de avaliação é pequeno e incompleto; a correção **não está validada para uso agrícola**. Não há série corrigida completa para todas as fases. Multiplicar a chuva não cria eventos ausentes nem desloca a data da chuva. Pode mudar a classificação de dias perto de 1 mm e, assim, alterar sequências sem corrigir sua causa.

## Hipóteses e pontos não verificados

- **Medido:** diferenças de volume e frequência; falhas da estação; células distintas do POWER; IMERG mais próximo ou mais distante em cada métrica conforme as tabelas. A escala espacial e o fechamento de dias são conhecidos.
- **Hipóteses:** chuva convectiva dentro das células, limitações do produto e possíveis falhas do pluviômetro podem contribuir. Não atribuímos a discrepância de 2025 a uma falha específica da NASA nem a seca real sem outra evidência.
- **Não verificado:** calibração e manutenção da A025, mudanças de local, comparação com pluviômetros vizinhos e radar, motivo físico da diferença recente e eventual participação desta estação nos pluviômetros usados na calibração do IMERG. IMERG Final usa ajuste por pluviômetros; sua validação contra uma estação não é necessariamente independente desse ajuste.
- Os CSV INMET não trazem bandeira de qualidade por valor de chuva. O controle aplicado detecta ausência, duplicação e valores inválidos; não certifica o sensor. POWER não fornece incerteza diária para PRECTOTCORR nesta resposta.
- Os sete anos locais não formam amostra aleatória ou série contínua. Não calculamos tendência climática nem probabilidade de perda para a próxima safra.

## Efeito na decisão agrícola

A inspeção encontrou o plano inicial do projeto com uma proposta de ETo FAO-56, Kc por fase e perda FAO-33, mas **não encontrou `app/regras/`, modelo executável ou parâmetros agronômicos rastreáveis**. Os scripts existentes fora desta pesquisa pertencem às skills de negócio. Não criamos um modelo novo para completar resultados.

Faltam: capacidade de água disponível e profundidade efetiva de raízes por solo; regra de infiltração, drenagem e escoamento; estado inicial da água e período de aquecimento; data de plantio e duração das fases por cultivar; Kc e Ky com fontes regionais; cálculo e validação de ETo com dias alinhados; produtividade potencial e validação independente. Para margem, faltam preços locais datados e escopo de custos coerente. As produtividades das planilhas Conab são premissas de orçamento, não resposta medida à chuva. Cobertura ainda exige espécie, ciclo, custos e objetivo agronômico; não atribuímos receita ou benefício futuro fictício.

Quando houver modelo, manter iguais solo, plantio, culturas, outras variáveis, custos e preços; mudar só a chuva. Preferir temporadas completas, com água inicial observada ou aquecimento documentado. Não unir trechos separados por falhas nem reiniciar o solo em capacidade de campo sem justificativa. Não calculamos déficit, produtividade ou margem nesta pesquisa. **Não foi possível provar se a fonte muda a ordem milho × sorgo × cobertura.**

## O que o aplicativo deve mostrar

- Fonte, versão, célula ou estação, escala, período, dia UTC e data de obtenção.
- Quantos dias válidos entraram no resultado e se o acumulado é completo ou pareado parcial.
- A diferença local do IMERG e do POWER; ausência não é chuva zero.
- Limites do histórico: sete anos isolados, falhas da estação e IMERG disponível até setembro/2025 no catálogo consultado.
- Frequência histórica não é previsão. Sem modelo e parâmetros validados, não mostrar ranking econômico como conclusão desta pesquisa.

## Acesso, reprodução e arquivos

O bloqueio anterior de EULA **não se repetiu**: download oficial com a credencial já existente retornou 200 e um NetCDF real. O OPeNDAP `.dds` retornou 400 porque DAP2 não representa variáveis Int8. O endpoint **DAP4 `.dap.nc4`** funcionou e forneceu recortes da célula. Isso é uso normal da autenticação oficial. Nenhum segredo foi gravado nos resultados. `imerg_access.json` preserva o teste inicial; os recortes e seus metadados comprovam o acesso posterior por DAP4.

Comandos usados, a partir da raiz:

```bash
uv venv /tmp/nasa26-rain-venv
uv pip install --python /tmp/nasa26-rain-venv/bin/python -r scripts/requirements-chuva.txt
python scripts/chuva_fontes.py
python scripts/chuva_imerg_probe.py
python scripts/chuva_imerg.py
/tmp/nasa26-rain-venv/bin/python scripts/chuva_analise.py
/tmp/nasa26-rain-venv/bin/python scripts/chuva_comparar_imerg.py
/tmp/nasa26-rain-venv/bin/python scripts/chuva_verificar.py
/tmp/nasa26-rain-venv/bin/python scripts/chuva_relatorio.py
```

Para reproduzir **sem rede**, execute só os quatro últimos comandos com o ambiente instalado. Os arquivos brutos já estão no repositório de trabalho. Para nova obtenção, use o mesmo Python do ambiente nos três scripts de rede; o IMERG lê a credencial local, sem mostrá-la. O cache evita repetir downloads. A série de recortes tem {len(im)} dias, com hash e consulta por arquivo.

- `scripts/chuva_*.py`: obtenção, controle, análise, verificações e geração deste relatório.
- `data/raw/pesquisa_chuva/`: respostas originais, documentos oficiais, recortes NetCDF e consultas com data/hash.
- `data/processed/pesquisa_chuva/`: séries diárias, auditoria horária, volumes mensais, métricas por ano/época, sequências secas, fatores e avaliação, metadados e hashes.
- `docs/pesquisa_chuva/`: este relatório e gráficos PNG.

Verificações executadas: datas únicas; calendário e anos bissextos; horas esperadas; ausência mantida; unidades e bordas UTC dos NetCDF; contagem IMERG; somas mensais iguais às somas diárias pareadas; anos de ajuste e teste separados; igualdade entre células POWER; comparação independente de quatro dias INMET com o CSV bruto; igualdade de três variáveis entre o arquivo IMERG global e o recorte de 01/01/2025.

## Documentação oficial

- [INMET: arquivos anuais](https://portal.inmet.gov.br/dadoshistoricos) — os cabeçalhos CSV confirmam estação, coordenadas e altitude.
- [INMET: definição do acumulado horário](https://portal.inmet.gov.br/glossario/tempo).
- [POWER: API diária, UTC e LST](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
- [POWER: resolução das fontes](https://power.larc.nasa.gov/docs/services/).
- [POWER: meteorologia e PRECTOTCORR](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/#precipitation).
- [NASA CMR: coleção diária IMERG V07](https://cmr.earthdata.nasa.gov/search/collections.json?concept_id=C2723754864-GES_DISC) — versão, cobertura, contagens e fórmula da taxa diária.
- [IMERG: produto e formatos](https://gpm.nasa.gov/data/imerg).
- [IMERG diário V07: DOI](https://doi.org/10.5067/GPM/IMERGDF/DAY/07).
- [NASA Earthdata: busca da coleção](https://search.earthdata.nasa.gov/search/granules?p=C2723754864-GES_DISC).
'''
(F/'RELATORIO.md').write_text(text)
print('Report and metadata written')
