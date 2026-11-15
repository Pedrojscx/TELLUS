# D-009 / #71: limites de arquivo, geometria e prazo de processamento

**Estado: DECIDIDA pelo usuário em 2026-11-15 como HIPÓTESE OPERACIONAL do protótipo, revisável após a demo.**
O registro em `docs/sdd/DUVIDAS_ETAPA1.md` e na #71 fica com o Maestro.

Os limites ficam num arquivo único de configuração: `backend/src/tellus/contrato/limites.json`. Cada limite traz `valor`,
`unidade`, `status: "hipotese"`, `decisao: "D-009"`, `issue: "#71"`, `data: 2026-11-15` e
`revisao: "revisável após a demo"`. Os valores aparecem em `GET /api/contrato/versao` (`limites`).

| Chave | Valor | Onde é aplicado |
|---|---|---|
| `arquivo_max_bytes` | 20 MB (20.971.520 bytes), todos os formatos | `POST /api/car/upload` (HTTP 413 `arquivo_grande`). É o mesmo valor que o upload já aplicava, agora lido do arquivo único. Os formatos novos da #22 usarão a mesma chave |
| `arquivo_formatos` | KML, KMZ, GeoJSON, Shapefile .zip | Só registrado. Hoje existe apenas o shapefile .zip; KML, KMZ e GeoJSON dependem da #22 |
| `lavouras_por_envio` | 1 (Polygon ou MultiPolygon) | Pedido do contrato: `area` é uma única geometria. No upload, só registrado (o leitor de shapefile da 001 não mudou) |
| `vertices_total_max` | 10.000 (total da geometria) | Pedido do contrato: erro `vertices_excedidos` (origem "pedido", campo "geometria") pedindo para simplificar ou dividir. A geometria nunca é simplificada em silêncio |
| `area_max_ha` | 100.000 ha | Pedido do contrato: erro `area_excedida` pedindo para dividir |
| `processamento_prazo_s` | 60 s, síncrono, sem fila | `secoes.calcular`: o prazo é conferido depois de cada chamada de módulo. Se estourar, sai o erro `tempo_excedido` (HTTP 504, origem "contrato", sugestão de tentar de novo, já que o cache acelera a segunda chamada) |
| `vertices_por_anel_max` | 5.000 | Limite técnico que já existia na spec 001 (CAR), antes em `referencias/car/limites.json`. O CAR agora lê daqui; valor e comportamento não mudaram |

## Por que 10.000 vértices no total (medição)

A validação de autointerseção (`car.regras.anel_autointersecta`) faz uma varredura por x. Em contornos comuns o
custo é quase linear. No pior caso (contorno em dente de serra, com todos os segmentos cruzando a largura inteira)
o custo é O(n²) por anel.

Medição de 2026-11-15, nesta máquina, com `validar_poligono` e o limite real de 5.000 por anel:

| Geometria | Vértices | Tempo |
|---|---|---|
| Formato comum (contorno circular), 1 anel | 5.000 | 0,03 s |
| Formato comum, 2 anéis de 5.000 | 10.000 | 0,03 s |
| Formato comum, 4 anéis de 5.000 | 20.000 | 0,06 s |
| Pior caso (dente de serra), 1 anel | 5.000 | 10,19 s |
| Pior caso, 2 anéis de 5.000 | 10.000 | 21,94 s |
| Pior caso, 4 anéis de 5.000 | 20.000 | 43,81 s |
| Referência: pior caso num anel único de 10.000 (sem o limite por anel) | 10.000 | 44,36 s |

O que os números mostram:
- Com 20.000 vértices no pior caso, só a validação gasta 44 s dos 60 s, sem contar 006 e 007.
- Com 10.000 vértices (no máximo 2 anéis de 5.000), o pior caso fica em cerca de 22 s e sobra folga para o cálculo.
- O limite de 5.000 por anel continua necessário: sem ele, um anel único de 10.000 levaria 44 s no pior caso, o dobro dos 22 s em 2 anéis.

## Impacto

- **#96 (pedido)**: uma geometria acima dos limites não inicia o cálculo.
- **012**: mostrar as mensagens de "simplifique ou divida" e de "tente de novo".
- **001**: nenhum comportamento mudou. O CAR lê `vertices_por_anel_max` e `arquivo_max_bytes` do arquivo único, com os mesmos valores (5.000 e 20 MB).
- **009 (vegetação)**: `vegetacao/servico.py` ainda fixa `MAX_VERTICES = 5000` no próprio código. Fica como pendência da frente 009, fora deste escopo; o teste de arquivo único a nomeia como exceção.

## Limitações

- O prazo de 60 s é conferido entre chamadas de módulo (interrupção cooperativa). Uma chamada isolada mais longa que o prazo só é detectada quando termina.
- Esta versão não tem rota de cálculo (falta a 008). Por isso o `tempo_excedido` vive em `secoes.calcular` e no contrato.
- Os tempos dependem da máquina. É preciso medir de novo no servidor da demo.

### Limitações conhecidas (registradas pelo usuário em 15/11)

- **Prazo de 60 s só entre módulos:** o limite é verificado apenas entre as chamadas de módulo (clima, motor, economia) em `secoes.calcular`. Uma etapa isolada que demore mais que o prazo não é interrompida no meio. O estouro só é detectado quando ela termina.
- **A demo depende do cache IMERG quente de Rio Verde:** dentro dos 60 s, o cálculo só cabe com a série IMERG de Rio Verde já em cache ou versionada em `referencias/clima/rio_verde_go/`. Sem esse cache, a primeira chamada precisaria baixar a série do GES DISC (cerca de 20 min com 16 conexões, segundo o REGISTRO.md da spec 003) e estouraria o prazo. Conferido na `main` 4bc0647 (15/11, 01h55): a série versionada cobre a célula `-17.75_-50.95`, com IMERG `ok` em todos os 9.039 dias de 2001-01-01 a 2025-09-30, sem lacuna. Os 410 dias seguintes estão como `nao_publicado` (D-002), e há 1 dia sem POWER (2026-11-14). Num clone limpo, sem `data/raw` e sem rede, `secoes.calcular` roda em 0,61 s para as 3 culturas, e os testes de contrato e do motor passam (100). Fora da célula da A025, como na área do CAR em `-17.85_-51.05`, ainda vale o download.
