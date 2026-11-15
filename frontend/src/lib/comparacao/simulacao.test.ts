// Interruptor MARGEM_DO_BACKEND_DISPONIVEL: enquanto false, a margem recalculada localmente é só simulação de exemplo.
import { describe, expect, it } from "vitest";

import { carregarExemplo, MARGEM_DO_BACKEND_DISPONIVEL, type Premissa } from "./contrato-provisorio";
import { margemPrincipal, MOTIVO_AGUARDANDO_BACKEND, MOTIVO_SEM_COTACAO, simulacaoLocal, validarCotacao } from "./premissas";

const ex = carregarExemplo();
const ALT = ex.resultado.alternativas.find((a) => a.preco_premissa_id === "preco_sorgo")!;
const SORGO = ex.premissas.find((p) => p.id === "preco_sorgo")!;
const cot = validarCotacao(SORGO, { valor: "50", origem: "cooperativa X, Rio Verde", data: "2026-11-10" }, "2026-11-15").cotacao!;
const COM: Premissa[] = ex.premissas.map((p) => (p.id === "preco_sorgo" ? { ...p, cotacao: cot } : p));

describe("interruptor desligado (padrão da demo)", () => {
  it("o interruptor está false até a 008 com repasse entrar na main", () => {
    expect(MARGEM_DO_BACKEND_DISPONIVEL).toBe(false);
  });

  it("com cotação, a margem principal continua indisponível (nunca resultado nem zero)", () => {
    const m = margemPrincipal(ALT, COM);
    expect(m.cenarios.map((c) => c.margem_r_ha)).toEqual([null, null, null]);
    expect(m.motivo).toBe(MOTIVO_AGUARDANDO_BACKEND);
  });

  it("sem cotação, motivo de falta de cotação", () => {
    expect(margemPrincipal(ALT, ex.premissas).motivo).toBe(MOTIVO_SEM_COTACAO);
  });

  it("a simulação local vem marcada exemplo:true e eh_resultado:false", () => {
    const s = simulacaoLocal(ALT, COM)!;
    expect(s.exemplo).toBe(true);
    expect(s.eh_resultado).toBe(false);
    expect(s.cenarios.every((c) => typeof c.margem_r_ha === "number")).toBe(true);
    expect(s.cotacao).toEqual(cot);
  });

  it("sem cotação não há simulação; alternativa sem premissa exigida também não", () => {
    expect(simulacaoLocal(ALT, ex.premissas)).toBeNull();
    expect(simulacaoLocal(ex.resultado.alternativas[0], COM)).toBeNull();
  });
});

describe("interruptor ligado (quando o backend calcular)", () => {
  it("a margem principal vem da alternativa (backend) e a simulação local sai", () => {
    const comMargem = { ...ALT, cenarios: ALT.cenarios.map((c) => ({ ...c, margem_r_ha: 100 })) };
    expect(margemPrincipal(comMargem, COM, true).cenarios.map((c) => c.margem_r_ha)).toEqual([100, 100, 100]);
    expect(simulacaoLocal(comMargem, COM, true)).toBeNull();
  });
});
