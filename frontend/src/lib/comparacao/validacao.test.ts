import { describe, expect, it } from "vitest";

import type { EntradasComparacao } from "./contrato-provisorio";
import { lerNumero, validarData, validarEntradas, validarGrupo, validarMetodologia, validarSolo } from "./validacao";

const VALIDAS: EntradasComparacao = {
  area: { id_geometria: "abc", area_ha: 120, municipio: "Rio Verde", uf: "GO", confirmada: true },
  colheita_soja: "2026-02-10",
  solo: { modo: "textura", textura: "media" },
  grupo: "II",
  metodologia: "comparar_alternativas",
  cultura: null,
};

describe("validarData", () => {
  it.each(["2026-02-10", "2024-02-29", " 2026-12-31 "])("aceita %s", (d) => {
    expect(validarData(d)).toBeNull();
  });

  it.each([null, undefined, ""])("exige a data (%s)", (d) => {
    expect(validarData(d)).toBe("Informe a data da colheita da soja.");
  });

  it.each(["10/02/2026", "2026-2-10", "2026-02", "fevereiro", "2026-02-10T00:00"])("recusa formato %s", (d) => {
    expect(validarData(d)).toMatch(/formato/);
  });

  it("a mensagem de formato descreve o formato realmente aceito (AAAA-MM-DD)", () => {
    const msg = validarData("10/02/2026");
    expect(msg).toMatch(/AAAA-MM-DD/);
    expect(msg).not.toMatch(/dia\/mês\/ano/);
    // o exemplo citado na mensagem tem de ser aceito pela própria validação
    const exemplo = /\d{4}-\d{2}-\d{2}/.exec(msg ?? "")?.[0];
    expect(exemplo).toBeDefined();
    expect(validarData(exemplo)).toBeNull();
  });

  it.each(["2025-02-29", "2026-02-30", "2026-13-01", "2026-00-10", "2026-04-31", "2026-01-00"])(
    "recusa dia inexistente %s",
    (d) => {
      expect(validarData(d)).toBe("Essa data não existe no calendário.");
    },
  );
});

describe("lerNumero", () => {
  it.each([
    ["60", 60],
    ["60,5", 60.5],
    ["60.5", 60.5],
    ["  42 ", 42],
    ["-3", -3],
    ["0", 0],
  ])("%s → %s", (t, n) => {
    expect(lerNumero(t)).toBe(n);
  });

  it.each([null, undefined, "", "   "])("vazio (%s) pede um número", (t) => {
    expect(lerNumero(t)).toBe("Informe um número.");
  });

  it.each(["6 0", "1 000", "60 ,5", "- 3", "6\t0"])("espaço interno é inválido (%j)", (t) => {
    expect(lerNumero(t)).toBe("Use só números (ex.: 60 ou 60,5).");
  });

  it.each(["abc", "60mm", "1,2,3", "1.000,5", "60.", ".5", "1e3", "NaN", "Infinity"])("recusa %s", (t) => {
    expect(typeof lerNumero(t)).toBe("string");
  });
});

describe("validarSolo", () => {
  it.each(["arenosa", "media", "argilosa"] as const)("textura %s é válida", (t) => {
    expect(validarSolo({ modo: "textura", textura: t })).toBeNull();
  });

  it("textura fora da lista da spec 005 é recusada", () => {
    expect(validarSolo({ modo: "textura", textura: "siltosa" as never })).toBe("Textura inválida.");
  });

  it("água disponível em mm > 0 é válida", () => {
    expect(validarSolo({ modo: "mm", cad_mm: 60.5 })).toBeNull();
  });

  it.each([0, -10, Number.NaN, Number.POSITIVE_INFINITY])("mm = %s é recusado", (mm) => {
    expect(validarSolo({ modo: "mm", cad_mm: mm })).toMatch(/maior que zero/);
  });

  it("sem solo pede textura ou mm", () => {
    expect(validarSolo(null)).toMatch(/textura do solo ou informe a água/);
  });
});

describe("validarGrupo", () => {
  it.each(["I", "II", "III", "nao_sei"])("aceita %s", (g) => {
    expect(validarGrupo(g)).toBeNull();
  });

  it.each([null, undefined, "", "IV", "i", "não sei"])("recusa %s", (g) => {
    expect(validarGrupo(g)).not.toBeNull();
  });
});

describe("validarEntradas (cenário de aceite 1)", () => {
  it("entradas completas não têm erro", () => {
    expect(validarEntradas(VALIDAS)).toEqual([]);
  });

  it("área não confirmada bloqueia", () => {
    const e = { ...VALIDAS, area: { ...VALIDAS.area!, confirmada: false } };
    expect(validarEntradas(e).map((x) => x.campo)).toEqual(["area"]);
    expect(validarEntradas({ ...VALIDAS, area: null }).map((x) => x.campo)).toEqual(["area"]);
  });

  it("acumula todos os erros, na ordem dos campos", () => {
    const vazio: EntradasComparacao = { area: null, colheita_soja: null, solo: null, grupo: null, metodologia: null };
    expect(validarEntradas(vazio).map((x) => x.campo)).toEqual(["area", "colheita_soja", "solo", "grupo"]);
  });

  it("não exige metodologia nesta etapa", () => {
    expect(validarEntradas({ ...VALIDAS, metodologia: null })).toEqual([]);
  });
});

describe("validarMetodologia", () => {
  it("comparar alternativas dispensa cultura", () => {
    expect(validarMetodologia(VALIDAS)).toEqual([]);
  });

  it("cultura escolhida exige a cultura", () => {
    const e = { ...VALIDAS, metodologia: "cultura_escolhida" as const, cultura: null };
    expect(validarMetodologia(e).map((x) => x.campo)).toEqual(["cultura"]);
    expect(validarMetodologia({ ...e, cultura: "milho" })).toEqual([]);
  });

  it("sem metodologia → erro de metodologia, e herda os erros das entradas", () => {
    const e = { ...VALIDAS, metodologia: null, grupo: null };
    expect(validarMetodologia(e).map((x) => x.campo)).toEqual(["grupo", "metodologia"]);
  });

  it("metodologia desconhecida é recusada", () => {
    expect(validarMetodologia({ ...VALIDAS, metodologia: "outra" as never }).map((x) => x.campo)).toEqual(["metodologia"]);
  });
});
