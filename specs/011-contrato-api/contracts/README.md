# Contrato TELLUS — versão 1.1.0

- `pedido.schema.json` e `resposta.schema.json` são gerados dos modelos pydantic em `backend/src/tellus/contrato/modelos.py` (`python -m tellus.contrato.exemplos`).
- `exemplos/`: pedidos válidos e de erro, e uma resposta gravada a partir dos módulos reais 006 e 007 (Rio Verde/GO, série versionada, offline).

## Compatibilidade

| Mudança | Versão |
|---|---|
| Remover ou renomear campo, mudar tipo, unidade ou significado de estado | MAIOR |
| Campo opcional novo, seção nova (ex.: entrada da 008) | MENOR |
| Texto e correção sem efeito no formato | CORREÇÃO |

O servidor aceita pedidos do mesmo MAIOR com MENOR ≤ o seu. Os demais recebem `versao_incompativel`, com a lista `versoes_aceitas`.

### Novidade em 1.1.0

Uma edição da premissa de preço (`modulo: "economia"`, `id: "preco_r_saca"`) pode informar também
`origem_informada` e `data_informada` (data ISO `AAAA-MM-DD`). Os campos são opcionais, mas devem ser enviados juntos,
e não são aceitos em nenhuma outra premissa. A resposta os preserva em `premissas_editadas` e registra a cotação na
proveniência da seção econômica. Pedidos 1.0.x, que não têm esses campos, continuam aceitos sem alteração.

## Para a 012

O adaptador `frontend/src/lib/comparacao/contrato-provisorio.ts` troca os tipos provisórios por tipos gerados de `resposta.schema.json` / `pedido.schema.json` (ex.: `json-schema-to-typescript`) e `carregarExemplo()` por `POST` da rota de cálculo, quando ela existir. O mapeamento campo a campo está no `plan.md` §"Troca do adaptador da 012".
