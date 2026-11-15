# Contrato TELLUS — versão 1.0.0

- `pedido.schema.json` e `resposta.schema.json` são gerados dos modelos pydantic em `backend/src/tellus/contrato/modelos.py` (`python -m tellus.contrato.exemplos`).
- `exemplos/`: pedidos válidos e de erro, e uma resposta gravada a partir dos módulos reais 006 e 007 (Rio Verde/GO, série versionada, offline).

## Compatibilidade

| Mudança | Versão |
|---|---|
| Remover ou renomear campo, mudar tipo, unidade ou significado de estado | MAIOR |
| Campo opcional novo, seção nova (ex.: entrada da 008) | MENOR |
| Texto e correção sem efeito no formato | CORREÇÃO |

O servidor aceita pedidos do mesmo MAIOR com MENOR ≤ o seu. Os demais recebem `versao_incompativel`, com a lista `versoes_aceitas`.

## Para a 012

O adaptador `frontend/src/lib/comparacao/contrato-provisorio.ts` troca os tipos provisórios por tipos gerados de `resposta.schema.json` / `pedido.schema.json` (ex.: `json-schema-to-typescript`) e `carregarExemplo()` por `POST` da rota de cálculo, quando ela existir. O mapeamento campo a campo está no `plan.md` §"Troca do adaptador da 012".

## Histórico de versões

- **1.1.0 (15/11, LK)**, MENOR e compatível com pedidos 1.0.x:
  - a seção `recomendacao` passa a vir com a saída real da 008, com proveniência `zarc`, `motor`, `economia`, `percentis`, `ordenacao` e, quando houver, os valores informados pelo produtor;
  - `premissas_editadas[]` ganha `origem_informada` (texto) e `data_informada` (AAAA-MM-DD), opcionais e sempre juntos, que chegam à proveniência da margem na 007 e na 008;
  - grupo `nao_sei`: as seções por cultura viram não obrigatórias e o resultado por grupo fica na 008;
  - rota nova `POST /api/contrato/calcular`.
- **1.0.0 (15/11, Pedro)**: primeira versão; a 008 ainda pendente.
