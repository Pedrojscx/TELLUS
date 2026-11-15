import copy

import pytest

from tellus.contrato import exemplos, regras, secoes


@pytest.fixture(scope="session")
def _resposta_real():
    """Resposta montada com os módulos REAIS 006/007 (Rio Verde, série versionada, offline)."""
    return secoes.calcular(regras.normalizar_pedido(exemplos.PEDIDO_VALIDO))


@pytest.fixture
def resposta_real(_resposta_real):
    return copy.deepcopy(_resposta_real)


@pytest.fixture
def pedido_valido():
    return copy.deepcopy(exemplos.PEDIDO_VALIDO)
