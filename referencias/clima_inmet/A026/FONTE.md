# Chuva diária INMET A026 (MINEIROS-GO)

Gerada por `scripts/preparar_inmet_validacao.py` a partir dos arquivos anuais do portal do INMET (https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip, https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip).

- Estação em -17.45472222, -52.60111111. Período 2024-01-01 a 2025-12-31: 170 de 731 dias com 24 horas válidas.
- Usada só para conferir a chuva de satélite (validação local). Nunca entra no cálculo.
- Método: dia UTC D = soma das horas de 01:00 de D a 00:00 de D+1; só com 24 horas válidas (docs/pesquisa_chuva/RELATORIO.md).
