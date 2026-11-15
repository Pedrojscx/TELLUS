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
