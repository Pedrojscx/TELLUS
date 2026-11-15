"""Cache SINTÉTICO de umidade SMAP para testar sem rede e sem credencial.

Os valores abaixo foram inventados para teste e são marcados `sintetico: true`. Não são observações
da NASA e nunca devem ser apresentados como dado real.
"""

import pytest

from tellus.umidade import cliente

LAT, LON = -17.785278, -50.965  # Rio Verde-GO (caso de referência)
CEL_M09 = (1059, 1382)  # célula SPL3SMP_E/SPL4SMGP de Rio Verde (conferida com pyproj)


def _reg(dia, variante, valor, qualidade="0", situacao="ok"):
    return {"chave": f"{dia}T00:00:00.000Z", "periodo_inicio": f"{dia}T00:00:00.000Z",
            "periodo_fim": f"{dia}T23:59:59.999Z", "variante": variante, "valor": valor, "qualidade": qualidade,
            "situacao": situacao, "linha_arquivo": str(CEL_M09[0]), "coluna_arquivo": str(CEL_M09[1]),
            "granulo": f"SINTETICO_SMAP_L3_SM_P_E_{dia.replace('-', '')}.h5", "obtido_em": "2026-11-15"}


META_SINTETICA = {"produto": "SPL3SMP_E", "versao": "006", "versao_fonte": "fixture sintética",
                  "unidade_no_arquivo": "cm**3/cm**3", "url": "sintetico://teste", "obtido_em": "2026-11-15",
                  "sintetico": True}


@pytest.fixture
def cache_sintetico(tmp_path):
    regs = [
        _reg("2025-01-10", "AM", "0.312400", "0"),
        _reg("2025-01-10", "PM", "0.298000", "0"),
        _reg("2025-01-11", "AM", "", "65534", "sem_dado"),  # célula sem recuperação neste dia
        _reg("2025-01-12", "AM", "0.287000", "1"),  # sem qualidade recomendada
        # 2025-01-13: nenhum registro (sem passagem/arquivo)
        _reg("2025-01-14", "AM", "0.275500", "0"),
    ]
    cliente.gravar_cache(tmp_path, "SPL3SMP_E", "EASE2_M09", *CEL_M09, regs, META_SINTETICA)
    return tmp_path


@pytest.fixture
def cache_l4(tmp_path):
    regs = [{"chave": "2025-01-10T01:30:00.000Z", "periodo_inicio": "2025-01-10T00:00:00.000Z",
             "periodo_fim": "2025-01-10T03:00:00.000Z", "variante": "superficie", "valor": "0.301000",
             "qualidade": "", "situacao": "ok", "linha_arquivo": "", "coluna_arquivo": "",
             "granulo": "SINTETICO_SMAP_L4_SM_gph_20250110T013000.h5", "obtido_em": "2026-11-15"}]
    meta = {"produto": "SPL4SMGP", "sintetico": True, "obtido_em": "2026-11-15", "url": "sintetico://teste"}
    cliente.gravar_cache(tmp_path, "SPL4SMGP", "EASE2_M09", *CEL_M09, regs, meta)  # sem versão nem unidade
    return tmp_path
