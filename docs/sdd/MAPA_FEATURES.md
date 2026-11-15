# Mapa de features — etapa 1

Data: 2026-11-14. Escopo nacional, com validação inicial em Rio Verde/GO.
Esta é a ordem das specs, não um plano de implementação. Não há tarefas nem issues nesta etapa.

| Ordem / ID | Feature | Tipo | Dependências | Resultado para o produtor |
|---|---|---|---|---|
| 001 | [pesquisa-car-wfs](../../specs/001-pesquisa-car-wfs/spec.md) | pesquisa | nenhuma | Saber se a busca por CAR é viável e qual alternativa usar |
| 002 | [localizacao-propriedade](../../specs/002-localizacao-propriedade/spec.md) | funcional | 001 apenas para consulta por CAR; desenho e upload independem dela | Confirmar a área da lavoura |
| 003 | [dados-clima](../../specs/003-dados-clima/spec.md) | dados | 002 | Histórico de chuva e clima com qualidade e origem |
| 004 | [calendario-zarc](../../specs/004-calendario-zarc/spec.md) | dados | 002 | Plantar somente em períodos oficiais válidos |
| 005 | [base-solo-culturas](../../specs/005-base-solo-culturas/spec.md) | dados | 004 para classes oficiais | Conferir e editar parâmetros com fonte |
| 006 | [motor-hidrico-entressafra](../../specs/006-motor-hidrico-entressafra/spec.md) | cálculo | 003, 004, 005 | Comparar falta de água sem interromper o balanço na entressafra |
| 007 | [economia](../../specs/007-economia/spec.md) | cálculo | 002, 005, 006 | Comparar margens e conferir custos e preços |
| 008 | [recomendacao](../../specs/008-recomendacao/spec.md) | decisão | 004, 006, 007 | Escolher decêndio ou par cultura × decêndio |
| 009 | [vegetacao-modis-hls](../../specs/009-vegetacao-modis-hls/spec.md) | contexto | 002 | Ver sazonalidade e cobertura passada |
| 010 | [umidade-smap](../../specs/010-umidade-smap/spec.md) | contexto | 002 | Ver umidade regional com aviso de escala |
| 011 | [contrato-api](../../specs/011-contrato-api/spec.md) | contrato | 002–010; 009 e 010 são seções opcionais | Receber resultados e erros consistentes |
| 012 | [interface-web](../../specs/012-interface-web/spec.md) | experiência | 011; 009 e 010 não bloqueiam o fluxo principal | Completar a comparação, revisar fontes e editar premissas |
| 013 | [identidade-visual](../../specs/013-identidade-visual/spec.md) | design | 012 funcional | Reconhecer Tellus sem perder clareza e acesso |

## Motivos da ordem

- A pesquisa CAR vem primeiro para expor a incerteza de acesso. Seu fracasso não bloqueia desenho ou upload.
- Calendário vem antes da base para que a conversão de solo respeite a portaria de cada cultura.
- O motor precede economia e recomendação: ambas usam os mesmos resultados por ano histórico.
- O contrato vem após as specs de domínio para reunir significados e estados já descritos.
  Isso não obriga implementar os serviços antes de definir o contrato na etapa futura.
- Vegetação e SMAP são contexto opcional. Sua falta não invalida um cálculo com entradas completas.
- A identidade visual permanece posterior ao fluxo funcional, como solicitado.

## Limites e regras comuns

O produto atende todo o Brasil; disponibilidade e validade regional precisam ser demonstradas por recorte.
Rio Verde/GO é o caso de referência, não uma prova de validade nacional.
Milho, sorgo e planta de cobertura são o recorte inicial de segunda safra após soja.
Cobertura sem ZARC aplicável não recebe recomendação de plantio como se tivesse janela oficial.
Pousio é uma alternativa de manejo, não uma cultura com janela inventada.

As duas metodologias usam o mesmo motor e a mesma versão das premissas.
O risco ZARC e a frequência histórica de falta de água são medidas distintas.
Fontes, unidades e parâmetros pendentes constam na [base de referência](BASE_REFERENCIA_SOLO_CULTURAS.md).
As dúvidas permanecem em [DUVIDAS_ETAPA1.md](DUVIDAS_ETAPA1.md), sem respostas presumidas.
As decisões atuais substituem a arquitetura e as fontes provisórias de `docs/PLANO.md`.

## Estado da revisão

As specs são rascunhos para revisão humana. As checklists registram as lacunas reais.
Não executar as etapas seguintes do Spec Kit nem abrir issues durante esta etapa.
