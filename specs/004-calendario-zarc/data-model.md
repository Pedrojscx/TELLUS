# Data Model: 004-calendario-zarc

## Entrada ZARC (FR-001)

É guardada de forma compacta em `referencias/zarc/<safra>/<UF>.json`, em
`municipios[codigo_ibge][cultura][grupo][solo] = {riscos: "<36 caracteres>", portaria}`.

| Atributo | Onde |
|---|---|
| safra, manejo, UF | cabeçalho do arquivo (`safra`, `manejo`, `uf`) |
| portaria, data da portaria (vigência) | `conjuntos[]` por cultura × grupo, e `portaria` em cada solo |
| município | chave `codigo_ibge` |
| cultura | chave (ver `referencias/zarc/culturas.json`) |
| grupo | chave (`GRUPO I`, `GRUPO II`, `GRUPO III`) |
| classe de solo | chave (`AD1`…`AD6` ou `1`/`2`/`3` no sorgo) |
| decêndio e risco | posição 1 a 36 no texto; `0` = fora, `2` = 20%, `3` = 30%, `4` = 40% |
| proveniência | `conjuntos[]`: arquivo, sha256, data de obtenção, data da portaria |

## Calendario (resposta de `/api/zarc/calendario`)

```json
{
  "codigo_ibge": "...",
  "uf": "...",
  "cultura": "...",
  "safra": "...",
  "manejo": "...",
  "significado": "...",
  "disponivel": true,
  "grupo_informado": null,
  "grupos": [
    {
      "grupo": "...",
      "disponivel": true,
      "proveniencia": {
        "fonte": "...", "portaria": "...", "data_portaria": "...", "safra": "...",
        "vigente": true, "obtido_em": "...", "url": "...", "arquivo_sha256": "..."
      },
      "solos": [
        {"solo": "...", "rotulo_solo": "...", "janela": [{"decendio": 1, "risco_zarc_pct": 20}]}
      ]
    }
  ]
}
```

- `janela` lista só os decêndios com risco diferente de zero.
- `grupo_informado: null` quer dizer "não sei": vêm todos os grupos.
- Quando não há dados: `disponivel: false` e `motivo`, com `grupos: []`.

## ConsultaData (`/api/zarc/consulta`)

`{..., data, resultados: [{grupo, solo, rotulo_solo, decendio, dentro_da_janela, risco_zarc_pct, portaria}]}`

O campo `risco_zarc_pct` sempre vem com o `significado` explícito e nunca se mistura com o
risco hídrico (FR-005).
