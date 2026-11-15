# Quickstart: 001-localizacao

Guia para validar a spec de ponta a ponta. Os detalhes de campos estão em
[data-model.md](data-model.md) e [contracts/localizacao.openapi.yaml](contracts/localizacao.openapi.yaml).

## Pré-requisitos

- `uv` e Python 3.12 ou superior; Node 24 ou superior e npm.
- Rede só para o passo 1. As referências já vêm commitadas, então o passo 1 é opcional para quem
  só quer rodar.

## 1. (Opcional) Regerar as referências

```bash
uv run --project backend python scripts/preparar_localizacao.py
```

Resultado esperado: `referencias/localizacao/*.json` atualizados, `FONTE.md` com as datas e o
relatório no terminal (municípios 5.571, polígonos 5.570, estações operantes, praças ligadas ao
IBGE). Nenhuma praça pode ficar sem código IBGE; se ficar, o script falha e mostra o nome.

## 2. Testes

```bash
uv run --project backend pytest backend/tests/localizacao backend/tests/api -q
```

Resultado esperado, tudo passando:
- Rio Verde-GO: A025 a cerca de 0 km do ponto da estação, IMERG (-17,75; -50,95), POWER
  (-18,0; -51,25), código IBGE 5218805 (FR-015 / SC-002);
- as 10 capitais mais Rio Verde com o município certo (SC-003);
- Nova York, (95; 0), "abc" e um ponto no mar recusados com o código certo (SC-005);
- o mesmo ponto chamado duas vezes dá respostas idênticas (FR-013).

## 3. API

```bash
uv run --project backend uvicorn tellus.api.app:app --port 8000
curl "http://localhost:8000/api/localizacao/padrao"
curl "http://localhost:8000/api/municipios?busca=rio%20verde"
curl "http://localhost:8000/api/localizacao?lat=40.71&lon=-74.00"
```

Resultado esperado:
- `/padrao` traz `eh_demo: true` e as 5 referências, cada uma com `procedencia`;
- a busca traz Rio Verde-GO e Rio Verde de Mato Grosso-MS;
- Nova York dá HTTP 422 com `fora_do_brasil`.

## 4. Tela (teste manual, anotar o resultado no registro da equipe)

```bash
cd frontend && npm install && npm run dev
```

1. A tela abre com Rio Verde-GO selecionado e marcado como local da demonstração.
2. Buscar "goiania" (sem acento) leva a Goiânia-GO. As referências mostram a estação INMET e a
   praça Conab mais próxima, com a distância e o aviso de outro município.
3. Digitar -17.785, -50.965 dá Rio Verde-GO.
4. Clicar no mar ou fora do Brasil mostra a mensagem e mantém o local anterior.
5. Cronometrar: escolher um local leva menos de 30 s (SC-001).
6. Desligar a rede e recarregar: a busca e as coordenadas funcionam, e o mapa mostra o contorno
   do Brasil sem o fundo (SC-006).
