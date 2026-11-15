# Proposta para D-008 / #70: produto SMAP e regra de período

**Situação:** PROPOSTA em teste. A decisão #70 continua aberta. Este documento não fecha nem
responde a issue.
**Data do teste:** 2026-11-15 · Frente B (desenho, spec 010) · amostra real obtida pelo A1 - Maestro #2, com o `EARTHDATA_TOKEN` autorizado pelo usuário (carregado só no ambiente; nunca impresso nem gravado)

## 1. Proposta do usuário (hipótese operacional do protótipo)

| Item | Proposta | Situação no código |
|---|---|---|
| Produto | SMAP **SPL3SMP_E** (L3 Enhanced, EASE-Grid 2.0 de 9 km, superfície ≈ 0–5 cm) | `servico.PRODUTO_HIPOTESE`, `produto.situacao = "hipotese"` |
| Período | Observações **válidas** dos **últimos 30 dias**, com a data de cada uma e a contagem de válidas | `servico.JANELA_DIAS = 30`, parâmetro `janela_dias`, `regra_periodo.situacao = "hipotese"` |
| Exibição | Contexto regional de superfície com aviso de escala. Nunca medida do talhão nem entrada da recomendação | `regras.NATUREZA`, `regras.USO`, `aviso_escala` em todo item, testes de isolamento |

Regra de "válida" implementada: o valor não é de preenchimento (≠ -9999) e
`retrieval_qual_flag` tem **bit 0 = 0** ("Soil moisture retrieval has recommended quality").
Fonte: guia do usuário SPL3SMP_E **V006**, §2.5.3 "Data Flags", **Tabela 6 (Retrieval Quality Flag Definition)**.
AM e PM contam como observações separadas. O fim da janela é o último dia guardado no cache, e
não o relógio. Por isso o mesmo cache dá a mesma resposta.

## 2. Fontes consultadas

- NASA CMR, coleções (público): SPL3SMP_E **V006**, `C2938664763-NSIDC_CPRD`, DOI 10.5067/M20OXIZHY3RJ, resolução de 9 km.
- NASA CMR, variáveis UMM-Var: `Soil_Moisture_Retrieval_Data_AM/soil_moisture` e `..._PM/soil_moisture_pm`, em `cm**3/cm**3`, com fill -9999.0. O `retrieval_qual_flag` tem fill 65534. O arquivo traz `EASE_row_index` e `EASE_column_index`. Cópia em `referencias/umidade/cmr_variaveis_2026-11-15.txt`.
- Guia NSIDC SPL3SMP_E V006 (PDF, sha256 `637af534…a5ffd`):
  - §1.1: superfície ≈ 5 cm do topo, em m³/m³.
  - Pé nativo do radiômetro ≈ 36 km, interpolado por Backus-Gilbert (domínio ≈ 33 km) para a grade de 9 km.
  - AM: passagem descendente às 6h, hora solar local. PM: ascendente às 18h.
  - Tabela 5: grade global de 1624 × 3856, EPSG:6933.
  - Tabela 6: flag de qualidade.
- Conferência da grade: a fórmula de `regras.ease2_xy` coincide com o `pyproj` (EPSG:6933) até 1e-8 m.
- Detalhes em `referencias/umidade/FONTE.md`.

## 3. Amostra de Rio Verde/GO (ponto -17,785, -50,965)

| Verificação | Resultado | Como |
|---|---|---|
| Célula EASE2 de 9 km | **linha 1059, coluna 1382**. Centro (-17,75156, -50,92842), a ≈ 5,4 km do ponto. Célula de 9,01 km | `regras.celula_ease2`, conferida com pyproj (teste `test_celula_de_rio_verde`) |
| Acesso ao dado | **Exige Earthdata login.** Sem login, `data.nsidc.earthdatacloud.nasa.gov/...h5` responde **HTTP 302 → `urs.earthdata.nasa.gov/oauth/authorize`**. O OPeNDAP (`opendap.earthdata.nasa.gov/.../*.dmr.xml`) responde **HTTP 302 → `/login/urs`**. O CMR não pede login | `curl` em 2026-11-15 |
| Credencial | **Usada com autorização explícita do usuário.** O `EARTHDATA_TOKEN` de `~/tellus/.env` foi carregado só no ambiente do comando (`set -a; . ~/tellus/.env`), sem ser lido, impresso nem gravado. Varredura: 0 arquivos em `data/raw/umidade`, `referencias/umidade`, `backend`, `specs` e `scripts` contêm o token | `grep -F` com o valor só no ambiente → 0 |
| Grânulos nos últimos 30 dias (2026-10-17 a 2026-11-15) | **27 dias com grânulo** e 32 entradas no CMR, porque há reprocessamentos `_002`. Dias sem grânulo: **2026-10-18**, mais 2026-11-14 e 11-15, que ainda não foram publicados | bruto `data/raw/umidade/cmr/SPL3SMP_E_2026-10-17_2026-11-15.json` + `.meta.json` (sha256 `f43863df…868f`) |
| Latência de publicação | 1ª publicação (`_001`, 22 grânulos): mediana de **≈ 20 h** após o fim do dia UTC, mínimo de 12,4 h. O máximo, 382 h, reflete atualizações posteriores do registro no CMR | `updated` − `time_end` no CMR |
| Reprocessamento | Em 10 dias da janela ampla (out–nov), um `_002` substitui o `_001`. O cliente fica com o maior contador | `cliente.buscar_granulos`, teste `test_buscar_granulos_fica_com_o_reprocessamento_mais_recente` |
| Tamanho | ≈ 550–640 MB por arquivo diário. Por isso o cliente pede só a célula via OPeNDAP DAP4 (8 variáveis, 1×1) | `granule_size` no CMR; `cliente.restricao_dap4` |
| Formato real do recorte | OPeNDAP DAP4 `.dap.nc4` = **netCDF4/HDF5** (assinatura `\x89HDF`), com os grupos `Soil_Moisture_Retrieval_Data_AM`/`_PM`. Cada variável tem forma (1, 1); `soil_moisture` é float32 com `units = cm**3/cm**3` e `_FillValue -9999`; flag e índices são uint16 com `_FillValue 65534`. O arquivo traz mais `dim0`/`dim1`. **Igual ao HDF5 sintético dos testes** | recortes em `data/raw/umidade/opendap/SPL3SMP_E/` (≈ 38 kB cada) |
| Divergência corrigida no cliente | O OPeNDAP endereça o grânulo pelo **GranuleUR do CMR** (`SMAP_L3_SM_P_E_20261101_R19240_001.h5_1MMe51bJ`), não pelo nome do arquivo `.h5`. Com o nome do arquivo, o Hyrax responde **HTTP 404**. Agora o cliente usa o link OPeNDAP que o próprio CMR publica (com o GranuleUR como reserva) | `cliente.buscar_granulos`/`url_opendap`; `test_url_opendap_usa_o_granule_ur_do_cmr` |
| **Dias com grânulo (2026-10-17 a 2026-11-15)** | **27 de 30**. Faltam 2026-10-18 (sem grânulo no CMR) e 2026-11-14 e 11-15 (ainda não publicados) | CMR + 27 recortes brutos |
| **Observações AM/PM na célula L1059/C1382** | 54 possíveis (27 × 2), das quais **18 com valor** (10 AM, 8 PM) e **36 com preenchimento** (−9999: a célula ficou fora da faixa da passagem; 17 AM, 19 PM). Em todos os arquivos, os índices `EASE_row/column_index` com valor são (1059, 1382) | contagem direta nos brutos e `servico.contexto` (os dois batem) |
| **Válidas pelo bit 0 da `retrieval_qual_flag` (preenchimento excluído)** | **17** (10 AM e 7 PM). A flag é **8** nas 17 válidas e **9** em 1 não recomendada (2026-11-08 PM, 0,2161). O bit 3 está ligado em todas; o significado não foi verificado aqui e ele não entra na regra | idem |
| **Faixa de valores válidos** | **0,1897 a 0,3594 m³/m³** (média de 0,26). Mínimo em 2026-10-20 AM e máximo em 2026-10-28 PM | idem |
| **Distribuição** | 17 observações válidas em **12 dias distintos** (em 5 deles há AM e PM). O intervalo entre dias com observação válida vai de 1 a **3 dias**, no máximo. Os 2 dias finais da janela ainda não foram publicados | série `referencias/umidade/rio_verde_go/serie.csv` |
| Rota real | Com o router montado, `GET /api/umidade/contexto?lat=-17.785&lon=-50.965` passou de **404 `sem_cache`** para **200** com **17 itens** reais, todos com `aviso_escala` espacial e temporal, `dado_sintetico: false` e `origem_dados: cache`. Sem cache local, usa a série versionada (`origem_dados: referencia_versionada`, com aviso). Sem nenhuma das duas, continua 404 `sem_cache`, nomeando a origem | `tests/umidade/test_rio_verde.py` |

## 4. Compatibilidade com a spec 010

| Requisito | Atendido pelo desenho? | Evidência |
|---|---|---|
| FR-001 (só contexto regional) | Sim | `regras.item_contexto` é o único construtor e fixa `natureza`/`uso`; `test_isolamento.py` |
| FR-002 (produto, versão, célula, período, unidade, qualidade, resolução) | Sim. A versão e a unidade vêm do arquivo/coleção; o que falta fica `desconhecido` | `test_valor_valido_traz_todos_os_metadados_e_aviso`, `test_metadado_desconhecido_nunca_vira_confirmado` |
| FR-003 (aviso de escala) | Sim, espacial e temporal em todo item | `test_sc001_todo_valor_em_qualquer_cenario_tem_aviso` |
| FR-004 (não determina recomendação/produtividade) | Sim, estruturalmente. O teste comparativo depende da spec 008 | `test_nenhum_modulo_de_calculo_importa_umidade` |
| SC-001 (100% com aviso) | Sim com dados sintéticos; **falta a amostra real** | idem |
| SC-002 (célula ausente → indisponível) | Sim: preenchimento, dia sem grânulo e janela sem válidas viram indisponível, sem vizinho | `test_sc002_*`, `test_janela_parametrizavel_e_sem_validas_fica_indisponivel` |

## 5. Veredito

**SUSTENTA**, como hipótese operacional do protótipo, para Rio Verde-GO em 2026-10-17 a 2026-11-15.
SPL3SMP_E V006 com as observações válidas (bit 0 = 0) dos últimos 30 dias dá **17 observações
válidas**, de 0,19 a 0,36 m³/m³, com data e passagem (AM/PM). É uma série útil como contexto regional,
em 12 dias distintos e com no máximo 3 dias entre dias com observação válida. Todos os FR e SC da seção 4 continuam atendidos com dado real:
o SC-001 foi verificado em 17 de 17 itens, e o SC-002 em 36 preenchimentos mostrados como lacuna, sem vizinho.

Isso **não fecha a #70**. Produto e janela continuam `hipotese` no código. A decisão é do Maestro e do usuário.

**Alternativa fundamentada, caso outra região ou estação dê poucas válidas** (não adotada, padrão mantido):

- Ampliar a janela (`janela_dias`). Com a taxa observada (cerca de 0,57 válida por dia), 30 dias já
  bastam aqui. Numa estação chuvosa com mais flags não recomendadas, 45 a 60 dias compensariam. A
  mudança é só de parâmetro e continua sendo hipótese.
- **SPL4SMGP V008** (9 km, a cada 3 h, `sm_surface` de 0–5 cm): contínuo, sem lacunas de passagem, mas
  é **estimativa de modelo com assimilação**, não observação, e teria de aparecer como tal. Não tem
  flag de qualidade por célula neste cache.

## 6. Limitações

- A amostra real cobre **uma célula e uma janela de 30 dias** (fim de outubro e início de novembro de 2026, começo da estação chuvosa). Outra estação ou região pode ter outra taxa de válidas. Os testes de unidade continuam usando fixtures **sintéticas** (`sintetico: true`); `test_rio_verde.py` usa a série real versionada.
- A interpretação da flag usa só o bit 0. Os bits 1 a 3 são guardados, mas não filtram.
- O cache é por célula. A geometria que toca várias células gera um item por célula, sem média, porque a regra de agregação não foi decidida.
