// SC-001 (spec 014): o resultado real gravado de Rio Verde, traduzido, não tem frase em português.
import { describe, expect, it } from "vitest";
import resposta from "../../../../specs/011-contrato-api/contracts/exemplos/resposta_rio_verde.json";
import { paraResultado, type RespostaContrato } from "../comparacao/contrato";
import { etapasDaResposta, TEXTO_ESTADO_GERAL } from "../comparacao/etapas";
import { traduzirTexto } from "./traduzir";

const PORTUGUES = /[ãõçáéíóúâêô]|\b(não|com|sem|para|uma|dos|das|pelo|pela|safra|decêndio|cultura|margem|risco)\b/i;

describe("SC-001: resultado em inglês", () => {
  it("nenhum texto do resultado gravado fica em português", () => {
    const r = resposta as unknown as RespostaContrato;
    const res = paraResultado(r, "comparar_alternativas");
    const textos: string[] = [];
    const add = (s: unknown) => { if (typeof s === "string" && s.trim()) textos.push(s); };
    add(res.criterio_ordem);
    res.avisos.forEach((a) => add(a.mensagem));
    res.erros.forEach((e) => { add(e.mensagem); add(e.acao); });
    res.alternativas.forEach((a) => {
      add(a.cultura); add(a.decendio); a.premissas_usadas.forEach(add);
      a.proveniencia.forEach((p) => { add(p.qualidade); add(p.escala); });
    });
    res.contextos_opcionais.forEach((c) => { add(c.titulo); add(c.resumo); add(c.aviso_escala); });
    etapasDaResposta(r).forEach((e: any) => { add(e.rotulo); add(e.detalhe); });
    Object.values(TEXTO_ESTADO_GERAL).forEach(add);
    const sobra = textos.map(traduzirTexto).filter((t) => PORTUGUES.test(t));
    expect(sobra).toEqual([]);
  });
});
