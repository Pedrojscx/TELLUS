# Proposta para D-008 / #70: produto SMAP e regra de período

**Situação:** PROPOSTA em teste. A decisão #70 continua aberta. Este documento não fecha nem
responde a issue.
**Data do teste:** 2026-11-15 · **Frente B (spec 010)**

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
| Credencial no ambiente do agente | **Ausente.** `EARTHDATA_TOKEN` não está definido. O `.env` não foi lido (Princípio VIII) | `scripts/preparar_umidade.py` → código de saída 3 |
| Grânulos nos últimos 30 dias (2026-10-17 a 2026-11-15) | **27 dias com grânulo** e 32 entradas no CMR, porque há reprocessamentos `_002`. Dias sem grânulo: **2026-10-18**, mais 2026-11-14 e 11-15, que ainda não foram publicados | bruto `data/raw/umidade/cmr/SPL3SMP_E_2026-10-17_2026-11-15.json` + `.meta.json` (sha256 `f43863df…868f`) |
| Latência de publicação | 1ª publicação (`_001`, 22 grânulos): mediana de **≈ 20 h** após o fim do dia UTC, mínimo de 12,4 h. O máximo, 382 h, reflete atualizações posteriores do registro no CMR | `updated` − `time_end` no CMR |
| Reprocessamento | Em 10 dias da janela ampla (out–nov), um `_002` substitui o `_001`. O cliente fica com o maior contador | `cliente.buscar_granulos`, teste `test_buscar_granulos_fica_com_o_reprocessamento_mais_recente` |
| Tamanho | ≈ 550–640 MB por arquivo diário. Por isso o cliente pede só a célula via OPeNDAP DAP4 (8 variáveis, 1×1) | `granule_size` no CMR; `cliente.restricao_dap4` |
| **Observações válidas na célula em 30 dias (AM/PM, bit 0)** | **NÃO VERIFICADO.** Sem login, nenhum valor de umidade nem flag foi lido. **Nenhum número foi inventado** | bloqueio acima |

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

**NÃO SUSTENTA (ainda) como proposta verificada.** O bloqueio é de acesso, não de mérito:

- **Sustentado pelas fontes:** o produto existe e está ativo (V006, publicado até 2026-11-13). A grade de 9 km e a célula de Rio Verde estão conferidas. A latência é de cerca de 1 dia, o que basta para uma janela de 30 dias. A regra de qualidade está documentada (Tabela 6), a unidade e o fill vêm do CMR, e todos os FR/SC são atendíveis pelo desenho implementado.
- **Não sustentado:** a premissa central da janela, de que há observações válidas em número útil na célula em 30 dias, não foi medida. Um dia com grânulo não garante valor na célula. A cobertura do radiômetro tem faixas, e a recuperação pode ser marcada como sem qualidade recomendada (vegetação densa, RFI, água). Sem o valor e a flag reais não há contagem.

**Para destravar** (o usuário roda, com o token só no ambiente):

```
! cd ~/tellus-wt/010 && set -a && . ~/tellus/.env && set +a && uv run --project backend python scripts/preparar_umidade.py --lat -17.785 --lon -50.965 --dias 30 --exportar-referencia rio_verde_go
```

O script imprime a contagem `observacoes_validas`, `registros_sem_dado` e
`registros_qualidade_nao_recomendada`, além de cada data e flag. Ele grava o bruto em
`data/raw/umidade/` e a série derivada em `referencias/umidade/rio_verde_go/`. Com esse resultado,
o veredito pode virar "sustenta".

**Alternativa fundamentada, caso a contagem real seja baixa** (não decidida):

- **SPL4SMGP V008** (9 km, 3 h, `sm_surface` 0–5 cm). É contínuo, sem falhas de passagem, mas é **estimativa de modelo com assimilação**, não observação. Teria de aparecer como tal (a ficha já marca `natureza`). Não tem flag de qualidade por célula neste cache: qualidade `desconhecido`.
- Outra opção é manter o SPL3SMP_E e ampliar a janela. Essa mudança é só de parâmetro (`janela_dias`), mas também seria hipótese.

## 6. Limitações

- O código foi testado só com fixtures **sintéticas** (`sintetico: true`). O caminho real (CMR → OPeNDAP → cache) foi testado com transporte HTTP simulado, não contra a NASA. O formato exato do recorte DAP4 da NSIDC (nomes de grupo no `.dap.nc4`) precisa ser confirmado na primeira execução com token.
- A interpretação da flag usa só o bit 0. Os bits 1 a 3 são guardados, mas não filtram.
- O cache é por célula. A geometria que toca várias células gera um item por célula, sem média, porque a regra de agregação não foi decidida.
