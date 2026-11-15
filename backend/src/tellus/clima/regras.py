"""Regras puras de clima: pesos de células, chuva ponderada e métricas (Princípio VI)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from tellus.localizacao.regras import ponto_em_poligono

PASSO_IMERG = 0.1


def indice_celula(lat: float, lon: float) -> tuple[int, int]:
    return math.floor(round((lat + 90) / PASSO_IMERG, 9)), math.floor(round((lon + 180) / PASSO_IMERG, 9))


def pesos_celulas(geometria: dict, passo: float = 0.005) -> dict[tuple[int, int], float]:
    """Fração da área em cada célula IMERG de 0,1°.

    Ponto: peso 1 na célula que o contém. Polígono/MultiPolygon: amostragem regular com `passo`
    graus dentro do polígono; o peso é a fração das amostras em cada célula (soma 1).
    """
    tipo = geometria["type"]
    if tipo == "Point":
        lon, lat = geometria["coordinates"][:2]
        return {indice_celula(lat, lon): 1.0}
    if tipo not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"geometria não suportada: {tipo}")
    aneis = [geometria["coordinates"][0]] if tipo == "Polygon" else [p[0] for p in geometria["coordinates"]]
    xs = [x for a in aneis for x, _ in a]
    ys = [y for a in aneis for _, y in a]
    contagem: dict[tuple[int, int], int] = {}
    n_lat = max(1, round((max(ys) - min(ys)) / passo))
    n_lon = max(1, round((max(xs) - min(xs)) / passo))
    for i in range(n_lat):
        lat = min(ys) + (i + 0.5) * (max(ys) - min(ys)) / n_lat
        for j in range(n_lon):
            lon = min(xs) + (j + 0.5) * (max(xs) - min(xs)) / n_lon
            if ponto_em_poligono(lat, lon, geometria):
                c = indice_celula(lat, lon)
                contagem[c] = contagem.get(c, 0) + 1
    total = sum(contagem.values())
    if total == 0:  # polígono menor que o passo: usa o centro do retângulo
        return {indice_celula((min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2): 1.0}
    return {c: n / total for c, n in sorted(contagem.items())}


def chuva_ponderada(valores: Mapping[tuple[int, int], float | None], pesos: Mapping[tuple[int, int], float]) -> float | None:
    """Média ponderada; None se qualquer célula com peso > 0 estiver sem valor (nunca vira zero)."""
    soma = 0.0
    for c, w in pesos.items():
        if w <= 0:
            continue
        v = valores.get(c)
        if v is None:
            return None
        soma += w * v
    return soma


def metricas(referencia: Sequence[float], fonte: Sequence[float], limiar_chuva: float = 1.0) -> dict:
    """Total, viés %, MAE, RMSE e fração de dias com chuva ≥ limiar, nos dias pareados."""
    if len(referencia) != len(fonte) or not referencia:
        raise ValueError("séries pareadas precisam ter o mesmo tamanho e não ser vazias")
    n = len(referencia)
    tot_r, tot_f = sum(referencia), sum(fonte)
    dif = [f - r for r, f in zip(referencia, fonte)]
    return {
        "n": n,
        "total_ref_mm": round(tot_r, 2),
        "total_mm": round(tot_f, 2),
        "vies_pct": round((tot_f - tot_r) / tot_r * 100, 2) if tot_r else None,
        "mae_mm_dia": round(sum(abs(d) for d in dif) / n, 2),
        "rmse_mm_dia": round(math.sqrt(sum(d * d for d in dif) / n), 2),
        "frac_dias_chuva_pct": round(sum(1 for f in fonte if f >= limiar_chuva) / n * 100, 2),
        "frac_dias_chuva_ref_pct": round(sum(1 for r in referencia if r >= limiar_chuva) / n * 100, 2),
    }
