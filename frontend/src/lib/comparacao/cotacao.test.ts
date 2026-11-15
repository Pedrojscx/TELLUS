// Preço do sorgo como premissa do produtor (D-005): sem padrão, valor + origem + data obrigatórios,
// margem indisponível (nunca zero) sem cotação. `hoje` é fixo para o teste ser determinístico.
import { describe, expect, it } from "vitest";

import { carregarExemplo, premissasParaPedido, type Premissa } from "./contrato-provisorio";
import { MOTIVO_SEM_COTACAO, margensComCotacao, mesclarPremissas, validarCotacao, valorEmUso } from "./premissas";
import { hojeISO, validarDataCotacao } from "./validacao";

const HOJE = "2026-11-15";
const ex = carregarExemplo();
const SORGO = ex.premissas.find((p) => p.id === "preco_sorgo")!;
const ALT = ex.resultado.alternativas.find((a) => a.preco_premissa_id === "preco_sorgo")!;
const OK = { valor: "50", origem: "cooperativa X, Rio Verde", data: "2026-11-10" };

describe("fixture: preço do sorgo sem padrão", () => {
  it("não grava preço padrão e explica o porquê", () => {
    expect(SORGO.padrao).toBeNull();
    expect(SORGO.exige_cotacao).toBe(true);
    expect(SORGO.sem_padrao_motivo).toBe("Sem cotação oficial (CEPEA não cobre sorgo) — informe a sua");
    expect(SORGO.cotacao).toBeNull();
    expect(valorEmUso(SORGO)).toBeNull();
    expect(ALT.cenarios.every((c) => c.margem_r_ha === null)).toBe(true);
  });
});

describe("validarCotacao", () => {
  it("válida: guarda valor, origem e data", () => {
    expect(validarCotacao(SORGO, OK, HOJE)).toEqual({
      cotacao: { valor: 50, origem_informada: "cooperativa X, Rio Verde", data_informada: "2026-11-10" }, erros: [],
    });
  });

  it("aceita vírgula decimal e normaliza espaços da origem", () => {
    const r = validarCotacao(SORGO, { ...OK, valor: "52,5", origem: "  coop   Y  " }, HOJE);
    expect(r.cotacao).toMatchObject({ valor: 52.5, origem_informada: "coop Y" });
  });

  it("tudo vazio = sem cotação e sem erro (margem indisponível)", () => {
    expect(validarCotacao(SORGO, { valor: "", origem: " ", data: "" }, HOJE)).toEqual({ cotacao: null, erros: [] });
  });

  it.each([
    [{ valor: "0" }, "valor", "maior que zero"],
    [{ valor: "-3" }, "valor", "maior que zero"],
    [{ valor: "abc" }, "valor", "números"],
    [{ valor: "" }, "valor", "Informe o valor"],
    [{ valor: "501" }, "valor", "Fora da faixa"],
    [{ origem: "   " }, "origem", "de onde veio"],
    [{ data: "" }, "data", "Informe a data da cotação"],
    [{ data: "2026-02-30" }, "data", "não existe"],
    [{ data: "10/11/2026" }, "data", "AAAA-MM-DD"],
    [{ data: "2026-11-16" }, "data", "futuro"],
  ])("inválida %o → erro em %s, sem cotação", (ajuste, campo, trecho) => {
    const r = validarCotacao(SORGO, { ...OK, ...ajuste }, HOJE);
    expect(r.cotacao).toBeNull();
    const e = r.erros.find((x) => x.campo === campo);
    expect(e?.mensagem).toContain(trecho);
  });

  it("os três campos são obrigatórios: só o valor não basta", () => {
    const r = validarCotacao(SORGO, { valor: "50", origem: "", data: "" }, HOJE);
    expect(r.cotacao).toBeNull();
    expect(r.erros.map((e) => e.campo).sort()).toEqual(["data", "origem"]);
  });

  it("data de hoje é aceita", () => {
    expect(validarDataCotacao(HOJE, HOJE)).toBeNull();
    expect(hojeISO(new Date(2026, 10, 15, 23, 59))).toBe("2026-11-15");
  });
});

describe("margensComCotacao", () => {
  it("sem cotação: todas indisponíveis com motivo, nunca zero", () => {
    const m = margensComCotacao(ALT, ex.premissas);
    expect(m.cenarios.map((c) => c.margem_r_ha)).toEqual([null, null, null]);
    expect(m.motivo).toBe(MOTIVO_SEM_COTACAO);
    expect(m.cotacao).toBeNull();
  });

  it("com cotação: sacas × preço − custo, e a cotação volta para a proveniência", () => {
    const cot = validarCotacao(SORGO, OK, HOJE).cotacao!;
    const ps: Premissa[] = ex.premissas.map((p) => (p.id === "preco_sorgo" ? { ...p, cotacao: cot } : p));
    const m = margensComCotacao(ALT, ps);
    const esperado = ALT.cenarios.map((c) => Math.round(c.sacas_ha! * 50 - c.custo_r_ha!));
    expect(m.cenarios.map((c) => c.margem_r_ha)).toEqual(esperado);
    expect(m.motivo).toBeNull();
    expect(m.cotacao).toEqual(cot);
  });

  it("alternativa sem premissa exigida não muda", () => {
    const milho = ex.resultado.alternativas[0];
    expect(margensComCotacao(milho, ex.premissas).cenarios).toEqual(milho.cenarios);
  });
});

describe("pedido e sessão", () => {
  it("o pedido leva valor, origem e data da cotação (campos propostos para o contrato 1.1.0)", () => {
    const cot = validarCotacao(SORGO, OK, HOJE).cotacao!;
    const ps = ex.premissas.map((p) => (p.id === "preco_sorgo" ? { ...p, cotacao: cot } : p));
    expect(premissasParaPedido(ps)).toEqual([{
      modulo: "economia", id: "preco_r_saca", cultura: "sorgo_granifero_2a_safra", unidade: "R$/saca 60 kg",
      valor_novo: 50, origem_informada: "cooperativa X, Rio Verde", data_informada: "2026-11-10",
    }]);
  });

  it("sem cotação, nada do sorgo vai no pedido", () => {
    expect(premissasParaPedido(ex.premissas)).toEqual([]);
  });

  it("sessão antiga sem a premissa do sorgo continua funcionando", () => {
    const antiga = ex.premissas.filter((p) => p.id !== "preco_sorgo").map((p) => (p.id === "preco_milho" ? { ...p, editado: 70 } : p));
    const m = mesclarPremissas(ex.premissas, antiga);
    expect(m.find((p) => p.id === "preco_sorgo")!.cotacao).toBeNull();
    expect(m.find((p) => p.id === "preco_milho")!.editado).toBe(70);
  });
});
