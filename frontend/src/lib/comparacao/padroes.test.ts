import { describe, expect, it } from "vitest";
import margem from "./__margem_milho_rio_verde.json";
import { mapearPadroes } from "./padroes";

// Resposta real gravada de POST /api/economia/margem (Rio Verde-GO, milho 2ª safra, sem perda simulada).
describe("padrões reais do editor de premissas", () => {
  const p = mapearPadroes(margem, { classe: "AD4", cad_mm: 54.6, status: "hipotese" });
  it("preço do CEPEA, custo e produtividade da Conab, com fonte", () => {
    expect(p.preco_milho.padrao).toBe(67.34);
    expect(p.preco_milho.proveniencia.fonte).toContain("Cepea");
    expect(p.custo_milho.padrao).toBe(5889);
    expect(p.sacas_ha_milho.padrao).toBe(100);
    expect(p.sacas_ha_milho.proveniencia.fonte).toContain("Conab");
  });
  it("água disponível da classe do ZARC, marcada como hipótese quando vem da textura", () => {
    expect(p.cad_mm).toMatchObject({ padrao: 54.6, proveniencia: { situacao: "hipotese" } });
  });
  it("sem resposta do servidor: nenhum padrão (o editor fica no exemplo)", () => {
    expect(mapearPadroes(null, null)).toEqual({});
  });
});
