import { describe, expect, it } from "vitest";

import {
  ETAPAS_PROVISORIAS,
  TEXTO_SITUACAO,
  etapaAtual,
  etapasDaResposta,
  podeMostrarComoFinal,
  simular,
  situacao,
  type Etapa,
  type EstadoEtapa,
} from "./etapas";
import type { RespostaContrato } from "./contrato";

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

// ---------------------------------------------------------------- resposta real (#103)
import resposta from "../../../../specs/011-contrato-api/contracts/exemplos/resposta_rio_verde.json";
import type { RespostaContrato } from "./contrato";
import { TEXTO_ESTADO_GERAL, etapasDaResposta, etapasEmAndamento, textoErro } from "./etapas";

const real = resposta as unknown as RespostaContrato;

describe("#103: etapas da resposta real", () => {
  it("carregamento informa a etapa atual e não é final", () => {
    const et = etapasEmAndamento("calculando");
    expect(etapaAtual(et)?.id).toBe("calculando");
    expect(podeMostrarComoFinal(et)).toBe(false);
  });
  it("fonte com cache mostra a data; cada fonte aparece uma vez", () => {
    const fontes = etapasDaResposta(real).filter((e) => e.id.startsWith("fonte:"));
    expect(fontes.length).toBe(new Set(real.fontes!.map((f) => f.fonte)).size);
    expect(fontes.every((f) => f.estado === "cache" && f.detalhe?.includes("2026-11-14"))).toBe(true);
  });
  it("seção indisponível aparece como indisponível com motivo; resposta incompleta não é final", () => {
    const brq = etapasDaResposta(real).find((e) => e.id === "braquiaria_cobertura:economia")!;
    expect(brq.estado).toBe("falha");
    expect(real.final).toBe(false);
    expect(TEXTO_ESTADO_GERAL[real.estado_geral].texto).toMatch(/PARCIAL/);
  });
  it("falha sem cache e sucesso", () => {
    const falha = { ...real, fontes: [{ fonte: "NASA POWER", estado: "falha" as const, obtido_em: null, secao: "risco_hidrico" }] };
    expect(etapasDaResposta(falha)[0]).toMatchObject({ estado: "falha", detalhe: "fonte fora do ar, sem cópia guardada" });
    const ok = { ...real, fontes: [{ fonte: "NASA POWER", estado: "ok" as const, obtido_em: "2026-11-15", secao: "risco_hidrico" }] };
    expect(etapasDaResposta(ok)[0]).toMatchObject({ estado: "ok" });
  });
  it("erro acionável traz origem, cópia guardada e o que fazer", () => {
    expect(textoErro({ codigo: "x", mensagem: "Chuva indisponível.", origem: "NASA IMERG", cache_obtido_em: "2026-11-14", acao: "Tente mais tarde." }))
      .toBe("Chuva indisponível. Origem: NASA IMERG. Usando cópia guardada de 2026-11-14. O que fazer: Tente mais tarde.");
    expect(textoErro({ codigo: "x", mensagem: "Falhou.", origem: "SICAR", cache_obtido_em: null, acao: null })).toContain("Sem cópia guardada");
  });
});

describe("grupo \"não sei\": culturas calculadas por grupo na recomendação", () => {
  it("não aparecem como falha e as fontes de clima são listadas", () => {
    const sec = { estado: "indisponivel", obrigatoria: false, erro: null, avisos: [{ codigo: "grupo_nao_sei", mensagem: "x" }] };
    const r = {
      versao_contrato: "1.2.0", estado_geral: "final", final: true,
      recomendacao: { estado: "disponivel", conteudo: {}, proveniencia: [], avisos: [], erro: null },
      contextos: { vegetacao: { estado: "nao_solicitado", conteudo: null, avisos: [], erro: null },
                   umidade: { estado: "nao_solicitado", conteudo: null, avisos: [], erro: null } },
      avisos: [], erros: [], hipoteses: [],
      fontes: [{ fonte: "NASA GPM IMERG Final", estado: "cache", obtido_em: "2026-11-14", secao: "recomendacao" }],
      culturas: [{ cultura: "milho_2a_safra", risco_hidrico: sec, economia: sec }],
    } as unknown as RespostaContrato;
    const et = etapasDaResposta(r);
    expect(et.find((e) => e.id === "fonte:NASA GPM IMERG Final")).toMatchObject({ estado: "cache", detalhe: "cópia guardada de 2026-11-14" });
    expect(et.filter((e) => e.id.startsWith("milho_2a_safra")).map((e) => [e.estado, e.detalhe]))
      .toEqual([["ok", "por grupo, na recomendação"], ["ok", "por grupo, na recomendação"]]);
  });
});
