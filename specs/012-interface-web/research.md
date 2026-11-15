# Pesquisa: 012 Interface web

**Data:** 2026-11-15 · **Frente B** · branch `012-interface-web` (base `origin/main` 9525782)

## R1. Hipótese operacional para #72 / D-010 (acesso e dispositivos)

**Proposta do usuário, registrada como HIPÓTESE (não decidida):**
- web responsiva para celular e computador;
- internet necessária;
- sem login obrigatório para o produtor na demonstração;
- tudo sujeito à viabilidade das fontes.

**O que foi verificado em 2026-11-15** (requisições sem credencial, a partir do ambiente do agente):

| Fonte | Spec | Exige login no servidor? | Evidência |
|---|---|---|---|
| NASA SMAP SPL3SMP_E (NSIDC) | 010 | **Sim, Earthdata.** | `data.nsidc.earthdatacloud.nasa.gov/...h5` → HTTP 302 para `urs.earthdata.nasa.gov/oauth/authorize`; OPeNDAP → HTTP 302 para `/login/urs` |
| NASA MODIS MOD13Q1 v061 (LP DAAC) | 009 | **Sim, Earthdata.** | `data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD13Q1.061/...hdf` → HTTP 302 para URS |
| NASA HLS L30 v2.0 (LP DAAC) | 009 | **Sim, Earthdata.** | `.../lp-prod-protected/HLSL30.020/...B11.tif` → HTTP 302 para URS |
| NASA GPM IMERG Final (GES DISC) | 003 | Sim, Earthdata (`EARTHDATA_TOKEN`, já usado em `tellus.clima.imerg`) | REGISTRO.md, spec 003 |
| NASA CMR (busca de metadados) | 009/010 | Não | consultas públicas usadas na spec 010 |
| NASA POWER, IBGE, INMET, SISZARC, Conab, CAR WFS | 001–007 | Não, segundo o REGISTRO e a spec 004 FR-002 | REGISTRO.md |

**Conclusão sobre a viabilidade:**
- O "sem login" **do produtor** continua viável. O login Earthdata é do **servidor**, não do usuário: o servidor guarda `EARTHDATA_TOKEN` no ambiente (Princípio VIII) ou já tem um cache e uma série versionada (como `referencias/clima/rio_verde_go/`).
- **Impacto:**
  1. Uma demonstração sem token no servidor só mostra 003/009/010 para os locais com cache ou referência versionada. Nos outros locais aparece o erro legível `sem_cache`, que nomeia a origem.
  2. Os contextos 009/010 são opcionais, então a falta deles não bloqueia o fluxo principal.
  3. Já o IMERG (003) é obrigatório para o cálculo. Sem token e sem cache, o cálculo daquele local fica bloqueado com erro legível.
  4. Os termos de uso da Earthdata (uso da credencial do servidor para servir terceiros) **não foram avaliados**. É um ponto em aberto para a #72.
- A verificação não cobre requisitos de acessibilidade, navegadores mínimos nem o tamanho mínimo de tela. Isso é a parte "dispositivos" da #72 e continua pendente.

## R2. Reaproveitamento da localização (#57)

- `components/SeletorLocal.astro` (busca, coordenadas, mapa e CAR/SICAR) funciona sozinho e já chama endpoints existentes: `/api/localizacao*`, `/api/car/*` e `/api/lavoura/confirmar`.
- **Lacuna:** a confirmação (`confirmarArea`, linhas 215–227) não emite evento nem guarda a lavoura confirmada fora do próprio componente. A comparação não sabe que a área foi confirmada.
- **Gancho proposto** (não aplicado, porque o componente é compartilhado e não pode ser alterado nesta etapa): depois de `apiCar.confirmar`, chamar
  `document.dispatchEvent(new CustomEvent("tellus:area-confirmada", { detail: lav }))`.
  A comparação ouve esse evento e preenche `EntradasComparacao.area`. É uma linha, sem mudança de comportamento para a tela atual.
- O desenho no mapa e o arquivo genérico (spec 002) ainda não existem no frontend. O FR-001 da 012 ("três modos") depende da #19.

## R3. Dados que a 012 já pode consultar sem a 011

Endpoints reais que existem no `main`: `/api/culturas`, `/api/solo/classificar` (005), `/api/zarc/{culturas,calendario,consulta}` (004),
`/api/clima/*` (003) e, na branch 010, `/api/umidade/{produtos,contexto}`. As telas desta etapa **não os chamam**: a regra é
usar só dados de exemplo até o contrato versionado. O plano marca onde cada um entra.

## R4. Termos

- "Sacas colhidas por hectare" aparece só como **premissa econômica editável do produtor** na fixture de exemplo, porque a receita da margem (007) precisa dela. A fonte e o nome definitivos são da 007/008. Nenhum valor é derivado de vegetação ou umidade (009 FR-004, 010 FR-004).
- Nenhum texto usa "previsão". O risco histórico aparece como "frequência nos anos passados".
