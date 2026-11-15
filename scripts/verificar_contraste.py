"""Verifica o contraste (WCAG 2.1) das cores da identidade TELLUS lidas de frontend/src/styles/marca.css.

Uso: python scripts/verificar_contraste.py   (sai com código 1 se algum par ficar abaixo do mínimo)
Mínimo: 4,5:1 para texto normal (AA). Pares = como as cores aparecem de fato na tela.
"""

import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "frontend" / "src" / "styles" / "marca.css"
MINIMO = 4.5


def cores() -> dict[str, str]:
    return {m.group(1): m.group(2).lower() for m in re.finditer(r"--color-tellus-([a-z-]+):\s*(#[0-9a-fA-F]{6})", CSS.read_text(encoding="utf-8"))}


def luminancia(h: str) -> float:
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def pares(c: dict[str, str]) -> list[tuple[str, str, str]]:
    p = [(f"{t} sobre fundo", c[t], c["fundo"]) for t in ("texto", "texto-suave", "primaria", "destaque", "fonte", "hipotese", "aviso", "erro")]
    p += [(f"{t} sobre superficie", c[t], c["superficie"]) for t in ("texto", "texto-suave", "fonte", "hipotese", "aviso", "erro")]
    p += [(f"selo {t}", c[t], c[f"{t}-fundo"]) for t in ("fonte", "hipotese", "aviso", "erro")]
    p += [("branco sobre primaria (botão)", "#ffffff", c["primaria"]), ("branco sobre primaria-escura", "#ffffff", c["primaria-escura"])]
    return p


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    c = cores()
    falhas = 0
    for nome, frente, fundo in pares(c):
        r = contraste(frente, fundo)
        ok = r >= MINIMO
        falhas += not ok
        print(f"{'ok   ' if ok else 'FALHA'} {r:5.2f}:1  {nome}  ({frente} / {fundo})")
    print(f"\n{len(pares(c)) - falhas} de {len(pares(c))} pares ≥ {MINIMO}:1")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
