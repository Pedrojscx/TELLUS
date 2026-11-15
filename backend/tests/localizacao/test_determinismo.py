import json

from tellus.localizacao import servico
from tellus.localizacao.referencias import carregar


def test_mesmo_ponto_mesma_resposta():
    ref = carregar()
    a = servico.resolver(ref, -16.6869, -49.2648, meio="mapa")
    b = servico.resolver(ref, -16.6869, -49.2648, meio="mapa")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
