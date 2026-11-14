# Brief para o conselho

## Como avaliar
Isto é um projeto de hackathon (NASA Space Apps 2026, desafio "Field Shift": adaptar fazendas com dados NASA, com foco em rotação de culturas, saúde do solo e adaptação ao ambiente). Entrega em 15/11/2026 às 12h, horário de Brasília; restam cerca de 34 horas. Avalie o valor para o produtor e a viabilidade da demonstração. O voto FUND significa "vale construir neste prazo". Não avalie como empresa em busca de investimento. Critérios de banca conhecidos de um evento local: impacto, criatividade, validade, relevância e apresentação.

## A ideia
App web que ajuda o produtor de soja do Cerrado (candidato: Rio Verde-GO) a decidir, todo ano entre janeiro e março, o que plantar na segunda safra: milho safrinha, sorgo ou planta de cobertura. A decisão depende da data de colheita da soja.

O app:
1. Usa cerca de 40 anos de chuva e temperatura diárias do NASA POWER (grade de cerca de 50 km, baseada no modelo MERRA-2) para calcular, para cada data de plantio, a chance de falta de água na fase crítica de cada cultura.
2. Usa NDVI do MODIS (250 m, a cada 16 dias) para mostrar o histórico de vegetação da área.
3. Converte o risco em margem por hectare em três cenários (conservador, central, favorável), com custos da Conab e preços que o usuário pode editar.
4. Compara sequências de várias safras, incluindo o efeito da planta de cobertura.

## Fatos comprovados
- NASA POWER e MODIS NDVI respondem sem login; já temos respostas reais salvas.
- Um valor anual de chuva do POWER (2025) parece anômalo e ainda não foi conferido.

## Fatos não comprovados
- Nenhuma entrevista com produtor ou técnico.
- Nenhum custo da Conab, preço ou produtividade consultado.
- Regras agronômicas (fases críticas, perda de produtividade por falta de água, benefício da cobertura) ainda sem fonte.
- A região não está fechada.

## Alternativa existente
ZARC (zoneamento oficial do governo): dá janelas de plantio por município, cultura e solo, com nível de risco. Não mostra margem econômica nem compara sequências.

## Equipe e recursos
Cinco pessoas, um computador Linux, agentes de código (Claude Code e Codex). Só ferramentas gratuitas.
