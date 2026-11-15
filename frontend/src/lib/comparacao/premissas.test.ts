import { describe, expect, it } from "vitest";

import type { Premissa } from "./contrato-provisorio";
import { aplicarEdicao, diferenca, editadas, fmt, valorEmUso } from "./premissas";

const P: Premissa = {
  id: "preco_milho",
  nome: "Preço do milho",
  tipo: "economica",
  padrao: 50,
  editado: null,
  unidade: "R$/sc",
  minimo: 10,
  maximo: 200,
  proveniencia: { fonte: "exemplo", situacao: "hipotese" },
};

describe("aplicarEdicao", () => {
  it("valor válido vira editado, sem mexer no padrão", () => {
    const r = aplicarEdicao(P, "62,5");
    expect(r.erro).toBeNull();
    expect(r.premissa.editado).toBe(62.5);
    expect(r.premissa.padrao).toBe(50);
    expect(P.editado).toBeNull(); // não altera o objeto original
  });

  it("texto vazio volta ao padrão", () => {
    const r = aplicarEdicao({ ...P, editado: 70 }, "   ");
    expect(r).toEqual({ premissa: { ...P, editado: null }, erro: null });
  });

  it("valor igual ao padrão não conta como edição", () => {
    expect(aplicarEdicao({ ...P, editado: 70 }, "50").premissa.editado).toBeNull();
  });

  it.each(["10", "200"])("limites são inclusivos (%s)", (t) => {
    expect(aplicarEdicao(P, t).erro).toBeNull();
  });

  it.each(["9,99", "200.01", "-5"])("fora da faixa (%s): erro claro e mantém o valor anterior", (t) => {
    const antes = { ...P, editado: 70 };
    const r = aplicarEdicao(antes, t);
    expect(r.erro).toBe("Fora da faixa aceita: de 10 a 200 R$/sc.");
    expect(r.premissa).toBe(antes);
  });

  it("texto não numérico: erro e mantém o valor anterior", () => {
    const antes = { ...P, editado: 70 };
    const r = aplicarEdicao(antes, "abc");
    expect(r.erro).toMatch(/Use só números/);
    expect(r.premissa).toBe(antes);
  });
});

describe("valorEmUso, diferenca, editadas", () => {
  it("usa o editado quando existe, senão o padrão", () => {
    expect(valorEmUso(P)).toBe(50);
    expect(valorEmUso({ ...P, editado: 60 })).toBe(60);
    expect(valorEmUso({ ...P, editado: 0, minimo: 0 })).toBe(0); // zero editado não volta ao padrão
  });

  it("diferença absoluta e percentual (padrão × editado)", () => {
    expect(diferenca(P)).toBeNull();
    expect(diferenca({ ...P, editado: 60 })).toEqual({ absoluta: 10, percentual: 20 });
    expect(diferenca({ ...P, editado: 40 })).toEqual({ absoluta: -10, percentual: -20 });
  });

  it("padrão zero: percentual indefinido (null), sem dividir por zero", () => {
    expect(diferenca({ ...P, padrao: 0, minimo: -10, editado: 5 })).toEqual({ absoluta: 5, percentual: null });
  });

  it("padrão negativo: percentual sobre o valor absoluto", () => {
    expect(diferenca({ ...P, padrao: -50, minimo: -100, editado: -25 })).toEqual({ absoluta: 25, percentual: 50 });
  });

  it("editadas filtra só as premissas alteradas", () => {
    const ps = [P, { ...P, id: "b", editado: 60 }, { ...P, id: "c", editado: 0 }];
    expect(editadas(ps).map((p) => p.id)).toEqual(["b", "c"]);
  });
});

describe("fmt", () => {
  it("formata em pt-BR com até 2 casas", () => {
    expect(fmt(1234.5)).toBe("1.234,5");
    expect(fmt(10)).toBe("10");
    expect(fmt(3.14159)).toBe("3,14");
    expect(fmt(3.14159, 0)).toBe("3");
  });
});
