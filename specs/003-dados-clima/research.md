# Research: 003-dados-clima

Testes feitos em 2026-11-14, entre 23h45 e 23h55 BRT, na máquina do LK.

## R1. IMERG Final diário: acesso e formato

- **Decision**: OPeNDAP DAP4 da NASA, coleção `C2723754864-GES_DISC` (GPM_3IMERGDF V07B). Um
  pedido por dia, recortado para uma célula: `precipitation`, `precipitation_cnt`, `lat` e `lon`.
  A resposta vem em `.dap.nc4`, lida com h5py. O token vai como `Authorization: Bearer`, lido de
  `EARTHDATA_TOKEN`.
- **Evidence**:
  - HTTP 200 em cerca de 1,6 s por dia; 24 dias em 3,8 s com 12 conexões.
  - Os valores de 01 a 03/01/2025 (2,035; 16,28; 7,55 mm) são iguais aos de
    `data/processed/pesquisa_chuva/imerg_daily.csv`.
  - Índices da célula: lat = floor((lat+90)/0,1), lon = floor((lon+180)/0,1). A A025 cai em
    lat 722 e lon 1290, os mesmos da pesquisa.
  - O array vem na ordem [time][lon][lat].
- **Rejected**:
  - `.dap.csv`: HTTP 200, mas os valores vêm vazios.
  - DAP2 `.dds`: dá 400 por causa de Int8 (já estava no REGISTRO).
  - Download do arquivo global: cerca de 30 MB por dia, contra 25 KB do recorte.
- **Custo**: 2001-01-01 a 2025-09-30 são 9.039 dias. Com 16 conexões, leva uns 15 a 25 minutos
  por célula na primeira vez; depois vem do cache.

## R2. Lacuna depois de set/2025 (D-002)

- **Evidence**: 01/10/2025 e os dias seguintes dão HTTP 404 (granule inexistente).
- **Decision**: segue a recomendação do DUVIDAS_ETAPA1, que é recusar a lacuna. A série termina
  no último dia publicado. Cada dia 404 fica gravado como `nao_publicado`. A resposta informa
  `ultimo_dia_publicado`, e um pedido de período que passe dessa data recebe o aviso
  `lacuna_imerg`. Nenhum outro produto (Late/Early) substitui o Final em silêncio.

## R3. NASA POWER diário (variáveis da ETo)

- **Decision**: `GET https://power.larc.nasa.gov/api/temporal/daily/point` com
  `parameters=T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,RH2M,WS2M,PRECTOTCORR`, `community=AG`,
  `time-standard=UTC` e `format=JSON`, num só pedido para o período inteiro.
- **Evidence**: HTTP 200, 907 KB e 2,4 s para 2001 a 2025 (9.131 dias). O fill value é -999, mas
  não apareceu nenhum nesse ponto. A geometria devolve a altitude da célula (731,58 m). As fontes
  são MERRA2, SYN1DEG e POWER.
- **Regra**: `PRECTOTCORR` só é guardado para a comparação de fontes e nunca vai para a série de
  cálculo (constituição 1.1.0).

## R4. INMET (validação local)

- **Evidence**: `apitempo.inmet.gov.br/estacao/{inicio}/{fim}/{codigo}` responde HTTP 204, sem
  dados abertos. O caminho que funcionou na pesquisa foram os ZIPs anuais do portal
  (`portal.inmet.gov.br/dadoshistoricos`), de dezenas de MB por ano e com todas as estações.
- **Decision**: a A025 usa a série diária já validada pela pesquisa, versionada em
  `data/processed/pesquisa_chuva/daily_all_sources.csv` (coluna `inmet` e `paired`, 24 horas
  exigidas). Para as outras estações, a resposta declara a lacuna (`validacao_indisponivel`) com
  o motivo. O download dos ZIPs anuais fica como tarefa futura.

## R5. Área que cruza células (FR-002)

- **Decision**: os pesos das células vêm da fração da área da lavoura em cada célula de 0,1°. Ela
  é estimada por amostragem regular de 0,005° dentro do polígono (até 400 pontos por célula),
  sem biblioteca geoespacial. Um ponto ou uma área toda dentro de uma célula dá peso 1.
- **Regra de ausência**: se uma célula com peso maior que 0 não tem dado num dia, aquele dia fica
  ausente. Os pesos não são renormalizados e o dia não vira zero.
- **Note**: hoje a 002 entrega só ponto (entrega 1). O cálculo de pesos já aceita polígono
  GeoJSON e fica pronto para quando a 002 entregar o desenho.

## R6. Rastreabilidade (Princípio I)

Cada série entregue leva `fonte`, `versao`, `periodo` (início e fim), `unidade`, `localizacao`
(células e pesos, ou célula POWER com altitude) e `qualidade` (dias válidos, ausentes, não
publicados e contagem média do IMERG).

## R7. Cache e dados da demo

- O cache bruto fica em `data/raw/clima/imerg/<celula>.csv` e `data/raw/clima/power/<ponto>.json`,
  fora do Git.
- Para a demo rodar sem rede em qualquer máquina, a série de Rio Verde-GO é exportada para
  `referencias/clima/rio_verde_go/` (um CSV derivado com chuva IMERG e as variáveis POWER, mais o
  `FONTE.md` com hash e data). O serviço procura primeiro o cache local e depois as referências.
