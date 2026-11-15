"""Relatório das mensagens do backend sem inglês no catálogo (spec 014, SC-003).

Uso: uv run --project backend python scripts/i18n_faltantes.py
Varre os textos em português do código (fora docstrings), troca cada campo de f-string por um valor de exemplo e
lista os que o catálogo backend/src/tellus/i18n/en.json não traduz. Pedaços de frase montados na hora, cabeçalhos
de planilha e listas internas aparecem aqui sem problema: o que importa é a mensagem inteira, coberta pelos modelos.
"""

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend" / "src"))
from tellus import i18n  # noqa: E402

achados: dict[str, str] = {}
for f in sorted((RAIZ / "backend" / "src" / "tellus").rglob("*.py")):
    if "i18n" in f.parts:
        continue
    arvore = ast.parse(f.read_text(encoding="utf-8"))
    docs = {id(n.body[0].value) for n in ast.walk(arvore)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    for n in ast.walk(arvore):
        if isinstance(n, ast.JoinedStr):
            s = "".join(str(v.value) if isinstance(v, ast.Constant) else "{x}" for v in n.values)
            docs |= {id(v) for v in n.values if isinstance(v, ast.Constant)}
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
            s = n.value
        else:
            continue
        if len(s) > 12 and " " in s and "\n" not in s.strip() and i18n.parece_portugues(s):
            achados.setdefault(s, str(f.relative_to(RAIZ)))

faltam = {s: f for s, f in achados.items() if i18n._traduzir_ou_none(s.replace("{x}", "Q7")) is None}
for s, f in sorted(faltam.items(), key=lambda x: x[1]):
    print(f"{f} | {s}")
print(f"\n{len(achados)} textos em português; {len(faltam)} sem inglês no catálogo (inclui pedaços e textos internos).")
