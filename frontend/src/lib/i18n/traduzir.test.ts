import { describe, expect, it } from "vitest";
import { FRASES } from "./en";
import { datasEn, numerosEn, traduzirNo, traduzirTexto } from "./traduzir";

describe("spec 014: tradução PT → EN", () => {
  it("frase inteira do dicionário", () => {
    expect(traduzirTexto("Calcular")).toBe("Calculate");
    expect(traduzirTexto("  Risco histórico de falta de água ")).toBe("Historical water-shortage risk");
  });
  it("preserva os espaços das pontas do nó", () => {
    expect(traduzirNo(" Solo\n")).toBe(" Soil\n");
  });
  it("números no formato do inglês, sem mudar o valor", () => {
    expect(numerosEn("R$ 5.889,09/ha e 67,34 e 10.000 ha")).toBe("R$ 5,889.09/ha e 67.34 e 10,000 ha");
    expect(numerosEn("contrato 1.1.0, data 2026-11-14, V07B")).toBe("contrato 1.1.0, data 2026-11-14, V07B");
    expect(numerosEn("-17,785; -50,965")).toBe("-17.785; -50.965");
  });
  it("datas sem ambiguidade", () => {
    expect(datasEn("colheita 20/01/2027, plantio 10/02")).toBe("colheita Jan 20, 2027, plantio Feb 10");
    expect(datasEn("IN 1/2022 e 45/99")).toBe("IN 1/2022 e 45/99");
  });
  it("frase montada na hora: trechos conhecidos", () => {
    expect(traduzirTexto("Padrões reais para Rio Verde-GO.")).toBe("Real defaults for Rio Verde-GO.");
    expect(traduzirTexto("decêndio 5 (plantio 11/02)")).toBe("10-day period 5 (planting Feb 11)");
  });
  it("frase do dicionário já vem com números em inglês (não converte de novo)", () => {
    expect(traduzirTexto("Usar área de exemplo (Rio Verde-GO, 35,15 ha)")).toBe("Use sample area (Rio Verde-GO, 35.15 ha)");
    // No navegador, cliente.ts guarda o que já escreveu em cada nó e nunca traduz o mesmo texto duas vezes.
  });
  it("nenhuma tradução fala em previsão (palavras proibidas em inglês, FR-010)", () => {
    const tudo = Object.values(FRASES).join(" ").toLowerCase();
    for (const p of ["forecast", "will rain", "predicted yield", "guaranteed"]) expect(tudo).not.toContain(p);
  });
});
