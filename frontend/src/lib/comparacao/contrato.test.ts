import { describe, expect, it } from "vitest";
import resposta from "../../../../specs/011-contrato-api/contracts/exemplos/resposta_rio_verde.json";
import { montarPedido, paraResultado, type RespostaContrato } from "./contrato";
import type { EntradasComparacao, Premissa } from "./contrato-provisorio";
import type { LavouraConfirmada } from "./lavoura";

const r = resposta as unknown as RespostaContrato;

const entradas: EntradasComparacao = {
  area: { id_geometria: "ponto", area_ha: 0, municipio: "Rio Verde", uf: "GO", confirmada: true, real: true },
  colheita_soja: "2027-01-20", solo: { modo: "textura", textura: "argilosa" }, grupo: "I",
  metodologia: "comparar_alternativas", cultura: null,
};
const ponto: LavouraConfirmada = { tipo: "ponto", lat: -17.785278, lon: -50.965, codigo_ibge: "5218805", municipio: "Rio Verde", uf: "GO", area_ha: null, confirmada_em: "2026-11-15" };
const sorgo: Premissa = {
  id: "preco_sorgo", nome: "Preço do sorgo", tipo: "economica", padrao: null, unidade: "R$/saca de 60 kg", minimo: 1, maximo: 500,
  proveniencia: { fonte: "produtor", situacao: "editado" }, exige_cotacao: true,
  cotacao: { valor: 55, origem_informada: "Cooperativa local de Rio Verde/GO", data_informada: "2025-01-15" },
  pedido: { modulo: "economia", id: "preco_r_saca", cultura: "sorgo_granifero_2a_safra" },
};

describe("montarPedido (contrato 1.1.0)", () => {
  it("ponto, grupo e cotação informada no formato do contrato", () => {
    const p = montarPedido(entradas, ponto, [sorgo]) as any;
    expect(p.versao_contrato).toBe("1.1.0");
    expect(p.area).toEqual({ tipo: "ponto", lat: -17.785278, lon: -50.965, confirmada: true, codigo_ibge: "5218805" });
    expect(p.grupo).toBe("GRUPO I");
    expect(p.solo).toEqual({ textura: "argilosa" });
    expect(p.premissas_editadas[0]).toMatchObject({ modulo: "economia", id: "preco_r_saca", valor_novo: 55, origem_informada: "Cooperativa local de Rio Verde/GO", data_informada: "2025-01-15" });
    expect(p.cultura).toBeUndefined();
  });

  it("área confirmada vai como geometria", () => {
    const geo: LavouraConfirmada = { ...ponto, tipo: "geometria", area_ha: 35, geometria: { type: "MultiPolygon", coordinates: [] }, id_geometria: "abc", origem: "car" };
    const p = montarPedido({ ...entradas, grupo: "nao_sei", solo: { modo: "mm", cad_mm: 55 } }, geo, []) as any;
    expect(p.area).toMatchObject({ tipo: "geometria", id_geometria: "abc", origem: "car", confirmada: true });
    expect(p.grupo).toBe("nao_sei");
    expect(p.solo).toEqual({ cad_mm: 55 });
  });
});

describe("paraResultado (resposta real gravada de Rio Verde)", () => {
  const res = paraResultado(r, "comparar_alternativas");
  it("não é exemplo e traz as alternativas reais da 008, na ordem", () => {
    expect(res.exemplo).toBe(false);
    expect(res.versao_contrato).toBe("1.1.0");
    expect(res.alternativas.length).toBe((r.recomendacao.conteudo.alternativas as unknown[]).length);
    expect(res.alternativas.length).toBeGreaterThan(0);
    expect(res.criterio_ordem).toContain("margem no cenário conservador");
  });
  it("riscos separados, margem por cenário e fontes em cada alternativa", () => {
    const a = res.alternativas[0];
    expect(a.cenarios.map((c) => c.cenario)).toEqual(["conservador", "central", "favoravel"]);
    expect(a.risco_zarc_pct).toBeGreaterThan(0);
    expect(a.proveniencia.length).toBeGreaterThan(0);
    expect(a.proveniencia.every((p) => p.fonte)).toBe(true);
    expect(a.decendio).toMatch(/^decêndio \d+ \(plantio \d\d\/\d\d\)$/);
  });
  it("cotação do sorgo aparece como hipótese/fonte informada, nunca como previsão", () => {
    const sorgoAlt = res.alternativas.find((a) => a.cultura.startsWith("Sorgo"));
    expect(sorgoAlt?.premissas_usadas.some((h) => h.includes("Cooperativa"))).toBe(true);
    expect(JSON.stringify(res).toLowerCase()).not.toContain("vai chover");
  });
  it("contextos opcionais com aviso de escala", () => {
    expect(res.contextos_opcionais.map((c) => c.id)).toEqual(["vegetacao", "umidade"]);
    expect(res.contextos_opcionais.every((c) => c.aviso_escala.length > 0)).toBe(true);
  });
});
