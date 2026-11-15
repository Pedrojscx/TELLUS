import { describe, expect, it } from "vitest";

import {
  ETAPAS_PROVISORIAS,
  TEXTO_SITUACAO,
  etapaAtual,
  podeMostrarComoFinal,
  simular,
  situacao,
  type Etapa,
  type EstadoEtapa,
} from "./etapas";

const ESTADOS: EstadoEtapa[] = ["pendente", "rodando", "ok", "cache", "falha"];

/** Todas as etapas provisórias com o mesmo estado, salvo as sobrescritas por id. */
function etapas(base: EstadoEtapa, por: Record<string, EstadoEtapa> = {}): Etapa[] {
  return ETAPAS_PROVISORIAS.map((e) => ({ ...e, estado: por[e.id] ?? base }));
}

const OBRIGATORIAS = ETAPAS_PROVISORIAS.filter((e) => e.obrigatoria).map((e) => e.id);
const OPCIONAIS = ETAPAS_PROVISORIAS.filter((e) => !e.obrigatoria).map((e) => e.id);

describe("parcial nunca é final", () => {
  it("a lista provisória tem obrigatórias e a etapa opcional de contextos", () => {
    expect(OBRIGATORIAS.length).toBeGreaterThan(0);
    expect(OPCIONAIS).toEqual(["contextos"]);
  });

  it.each(OBRIGATORIAS.flatMap((id) => (["pendente", "rodando"] as const).map((est) => [id, est] as const)))(
    "obrigatória %s em %s → carregando, não final",
    (id, est) => {
      const es = etapas("ok", { [id]: est });
      expect(situacao(es)).toBe("carregando");
      expect(podeMostrarComoFinal(es)).toBe(false);
    },
  );

  it.each(OBRIGATORIAS)("obrigatória %s em falha → bloqueado, não final", (id) => {
    const es = etapas("ok", { [id]: "falha" });
    expect(situacao(es)).toBe("bloqueado");
    expect(podeMostrarComoFinal(es)).toBe(false);
  });

  it("falha prevalece sobre etapa ainda rodando", () => {
    expect(situacao(etapas("ok", { clima: "falha", calculo: "rodando" }))).toBe("bloqueado");
  });

  it("varredura exaustiva: só é final se TODAS as obrigatórias estão ok ou cache", () => {
    // 5 estados ^ 6 obrigatórias = 15 625 combinações; a opcional varia junto
    const n = OBRIGATORIAS.length;
    let finais = 0;
    for (let k = 0; k < ESTADOS.length ** n; k++) {
      const por: Record<string, EstadoEtapa> = {};
      let r = k;
      OBRIGATORIAS.forEach((id) => {
        por[id] = ESTADOS[r % ESTADOS.length];
        r = Math.floor(r / ESTADOS.length);
      });
      por.contextos = ESTADOS[k % ESTADOS.length];
      const es = etapas("ok", por);
      const todasProntas = OBRIGATORIAS.every((id) => por[id] === "ok" || por[id] === "cache");
      expect(podeMostrarComoFinal(es)).toBe(todasProntas);
      if (todasProntas) finais++;
    }
    expect(finais).toBe(2 ** n);
  });

  it("sem nenhuma etapa obrigatória na lista não há como afirmar resultado final", () => {
    expect(situacao([])).toBe("carregando");
    expect(podeMostrarComoFinal([])).toBe(false);
    const soOpcional: Etapa[] = [{ id: "contextos", rotulo: "x", obrigatoria: false, estado: "ok" }];
    expect(podeMostrarComoFinal(soOpcional)).toBe(false);
  });

  it("texto de carregando avisa que é parcial", () => {
    expect(TEXTO_SITUACAO.carregando).toMatch(/parcial/);
    expect(TEXTO_SITUACAO.carregando).toMatch(/não é o resultado/);
  });
});

describe("opcional não bloqueia", () => {
  it.each(ESTADOS)("contextos opcionais em %s com obrigatórias ok → final", (est) => {
    const es = etapas("ok", { contextos: est });
    expect(situacao(es)).toBe("final");
    expect(podeMostrarComoFinal(es)).toBe(true);
  });

  it("opcional em falha e obrigatória com cache → final_com_cache", () => {
    expect(situacao(etapas("ok", { contextos: "falha", clima: "cache" }))).toBe("final_com_cache");
  });

  it("opcional ok não torna final uma obrigatória pendente", () => {
    expect(situacao(etapas("ok", { contextos: "ok", economia: "pendente" }))).toBe("carregando");
  });
});

describe("situação final", () => {
  it("todas ok → final", () => {
    expect(situacao(etapas("ok"))).toBe("final");
  });

  it("alguma obrigatória com cache → final_com_cache", () => {
    expect(situacao(etapas("ok", { zarc: "cache" }))).toBe("final_com_cache");
    expect(situacao(etapas("cache"))).toBe("final_com_cache");
  });
});

describe("etapaAtual", () => {
  it("prefere a etapa rodando", () => {
    expect(etapaAtual(etapas("pendente", { area: "ok", solo: "rodando" }))?.id).toBe("solo");
  });

  it("sem etapa rodando, devolve a primeira pendente", () => {
    expect(etapaAtual(etapas("ok", { economia: "pendente", calculo: "pendente" }))?.id).toBe("economia");
  });

  it("tudo terminado → null", () => {
    expect(etapaAtual(etapas("ok", { clima: "falha" }))).toBeNull();
  });
});

describe("simular (tela de exemplo)", () => {
  const total = ETAPAS_PROVISORIAS.length;

  it("sucesso: parcial em todo passo intermediário e final no fim", () => {
    for (let p = 0; p < total - 1; p++) expect(podeMostrarComoFinal(simular("sucesso", p))).toBe(false);
    // no passo total-1 só falta a opcional (rodando): já é final
    expect(situacao(simular("sucesso", total - 1))).toBe("final");
    expect(situacao(simular("sucesso", total))).toBe("final");
  });

  it("degradado: clima vem do cache e o fim é final_com_cache", () => {
    const fim = simular("degradado", total);
    expect(fim.find((e) => e.id === "clima")?.estado).toBe("cache");
    expect(situacao(fim)).toBe("final_com_cache");
  });

  it("falha: ao chegar no clima fica bloqueado e nunca vira final", () => {
    for (let p = 0; p <= total; p++) {
      const s = situacao(simular("falha", p));
      expect(s).not.toBe("final");
      expect(s).not.toBe("final_com_cache");
      if (p >= 2) expect(s).toBe("bloqueado");
    }
  });

  it("é determinística", () => {
    expect(simular("degradado", 4)).toEqual(simular("degradado", 4));
  });
});
