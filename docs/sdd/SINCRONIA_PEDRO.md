# Sincronia LK → Pedro (14/11/2026, 23h20)

Cole o texto abaixo na sua sessão (Claude Code ou Codex) depois de `git pull origin main`.

---

Você está no repositório TELLUS (NASA Space Apps 2026, desafio Field Shift, prazo dom 15/11 às
12h BRT). Enquanto você estava parado, o LK e o Claude Code dele avançaram. Antes de agir, leia
nesta ordem: `.specify/memory/constitution.md`, `docs/sdd/MAPA_SPECS.md`, o fim do `REGISTRO.md` e
`specs/001-localizacao/plan.md`. Resumo do que mudou:

## Decisões tomadas

1. **Constituição v1.0.0** em `.specify/memory/constitution.md`. Ela prevalece sobre o
   `docs/PLANO.md`, que fica como histórico. Os 7 princípios:
   - I. Todo número tem fonte, data e unidade; sem fonte, `"status": "hipotese"`, editável.
   - II. O resultado é estimativa regional em faixas, nunca o talhão, e não é previsão.
   - III. A chuva do POWER nunca entra no balanço, nem corrigida. Chuva = IMERG Final, com a
     estação INMET como referência local.
   - IV. Regras puras e determinísticas, cada uma com um caso calculado à mão.
   - V. Funciona offline na demo (cache com procedência).
   - VI. Escopo mínimo até o fluxo completo; extras só depois, cada um em sua spec.
   - VII. Segredos fora do Git.
2. **Cobertura: qualquer ponto do Brasil.** Onde faltar dado oficial do local, usa-se a
   referência mais próxima com a distância, ou declara-se a lacuna. Rio Verde-GO continua sendo o
   local da demo e da validação.
3. **Mapa das specs** (`docs/sdd/MAPA_SPECS.md`), na ordem dos labels: 001 localização, 002
   dados-clima, 003 zarc, 004 solo-culturas, 005 motor-hídrico, 006 economia, 007 recomendação,
   008 api, 009 web, 010 design, 011 vegetação (extra), 012 umidade-solo (extra).
4. **Terceira opção = braquiária solteira** (*Urochloa ruziziensis*). Referência ZARC: milho com
   braquiária (Portaria 337), com aviso.
5. **Pilha**:
   - backend Python ≥ 3.12 com `uv` e FastAPI em `backend/` (pacote `tellus`, layout `src/`);
   - frontend Astro 7, Tailwind 4 e Leaflet em `frontend/`.
6. **Estrutura que toda spec segue**:
   - código em `backend/src/tellus/<area>/` (`regras.py` puro, `servico.py`, rotas em
     `backend/src/tellus/api/<area>.py`);
   - testes em `backend/tests/<area>/`;
   - referências versionadas em `referencias/<area>/` com `FONTE.md`;
   - script de preparação em `scripts/preparar_<area>.py`;
   - brutos em `data/raw/<area>/` (fora do Git, só os `.meta.json` entram).
7. **Decisões dentro das specs** (todas revisáveis):
   - nível de custo Conab padrão = custo operacional;
   - produtividade de referência = premissa Conab;
   - intervalo de semeadura = 3 dias após a colheita da soja (hipótese);
   - solo começa na capacidade de campo (hipótese);
   - perda severa = 30% (hipótese);
   - ordenação da 007: dentro do ZARC primeiro, depois maior margem no cenário **conservador**,
     depois menor risco;
   - a explicação é por modelo de frase, sem IA.
8. **Commits do LK** saem só com o nome dele, sem linha `Co-Authored-By` de IA nem rodapé de
   ferramenta. Se puder, faça o mesmo nos seus.

## O que está feito

- Specs 001 a 007 escritas (`specs/NNN-*/spec.md` + checklist), cada uma na branch `NNN-nome`
  no GitHub.
- **001 implementada e já na `main`**:
  - `scripts/preparar_localizacao.py` gera `referencias/localizacao/` (IBGE com 5.571 municípios e
    a malha mínima, INMET com 668 estações, Conab com 27 praças de 2025/26 ligadas ao IBGE);
  - API: `GET /api/localizacao/padrao`, `/api/localizacao?lat&lon`,
    `/api/localizacao/municipio/{ibge}`, `/api/municipios?busca`;
  - tela de escolha do local;
  - 50 testes passando; Rio Verde confere com o REGISTRO.
- Rodar:
  ```bash
  cd backend && uv sync && uv run pytest -q
  uv run uvicorn tellus.api.app:app --port 8000
  cd frontend && npm install && npm run dev   # http://localhost:4321
  ```

## Achados que afetam as próximas specs

- Sorgo: a Conab só tem planilha 2025/26 em 4 praças (Barreiras-BA, Rio Verde-GO, Uberaba-MG,
  Pedro Afonso-TO). A spec 006 vai mostrar "custo de outra região" na maioria dos lugares.
- A planilha de milho 2ª safra fica em
  `.../agricolas/milho/milho_2a_safra_serie_historica_2005-2026.xls` (o link da página termina
  em `/view` e devolve HTML).
- Células: POWER = round(lat/0,5)·0,5 e round(lon/0,625)·0,625; IMERG = centro da célula de 0,1°.
  Ambas conferem com o REGISTRO. Em Rio Verde, a célula do POWER fica a 38 km do ponto (a grade
  é de cerca de 50 km).
- Boa Esperança do Norte-MT (5101837) ainda não tem polígono na malha do IBGE.

## Divisão proposta

- **LK + Claude**: 002 dados-clima agora, que é o caminho crítico (002 → 005 → 006 → 007).
- **Pedro**: 003 zarc (o fluxo do SISZARC já está no REGISTRO) e 004 solo-culturas (pesquisa de
  Kc, Ky e fases com fonte). As duas não dependem da 002.
- Depois: 005 → 006 → 007, e 008 e 009 integram.
- Para cada spec: `git switch NNN-nome && git merge main`, depois `/speckit-plan`, `/speckit-tasks`
  e `/speckit-implement`. Siga a estrutura do item 6 e só faça merge na `main` com os testes
  passando. Atualize o status no `MAPA_SPECS.md` e escreva no `REGISTRO.md`.
- Ao pegar uma spec, marque na issue correspondente para a gente não pegar a mesma.
