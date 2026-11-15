import time

from tellus.localizacao import busca, servico
from tellus.localizacao.referencias import carregar


def test_resolver_rapido():
    ref = carregar()
    servico.resolver(ref, -16.6869, -49.2648)  # aquece
    t0 = time.perf_counter()
    servico.resolver(ref, -12.9714, -38.5014)
    assert time.perf_counter() - t0 < 0.2


def test_busca_rapida():
    ref = carregar()
    t0 = time.perf_counter()
    busca.buscar(ref.municipios_ordenados, "sao")
    assert time.perf_counter() - t0 < 0.1
