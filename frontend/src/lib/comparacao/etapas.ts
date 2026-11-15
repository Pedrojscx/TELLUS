// Indicador de carga por etapas (#103). Puro.
// Regra: o resultado só é "final" quando TODAS as etapas obrigatórias terminaram (ok ou com
// cache). Qualquer etapa pendente, rodando ou com falha impede mostrar o resultado como final.
// A lista real vem da resposta do contrato 1.1.0 (etapasDaResposta); a provisória fica para a tela de exemplo.

import { NOME_CULTURA, type RespostaContrato } from "./contrato";
import type { ErroFonte } from "./contrato-provisorio";

export type EstadoEtapa = "pendente" | "rodando" | "ok" | "cache" | "falha";

export interface Etapa {
  id: string;
  rotulo: string;
  obrigatoria: boolean;
  estado: EstadoEtapa;
  detalhe?: string;
}

export const ETAPAS_PROVISORIAS: Omit<Etapa, "estado">[] = [
  { id: "area", rotulo: "Área confirmada", obrigatoria: true },
  { id: "zarc", rotulo: "Calendário ZARC", obrigatoria: true },
  { id: "clima", rotulo: "Chuva e clima (NASA)", obrigatoria: true },
  { id: "solo", rotulo: "Solo e culturas", obrigatoria: true },
  { id: "economia", rotulo: "Custos e preços", obrigatoria: true },
  { id: "calculo", rotulo: "Cálculo das alternativas", obrigatoria: true },
  { id: "contextos", rotulo: "Contextos opcionais (vegetação, umidade)", obrigatoria: false },
];

export type Situacao = "carregando" | "final" | "final_com_cache" | "bloqueado";

export function situacao(etapas: Etapa[]): Situacao {
  const obr = etapas.filter((e) => e.obrigatoria);
  // Sem nenhuma obrigatória (lista vazia ou ainda não recebida), nada foi calculado: não é final.
  if (obr.length === 0) return "carregando";
  if (obr.some((e) => e.estado === "falha")) return "bloqueado";
  if (obr.some((e) => e.estado === "pendente" || e.estado === "rodando")) return "carregando";
  return obr.some((e) => e.estado === "cache") ? "final_com_cache" : "final";
}

export function podeMostrarComoFinal(etapas: Etapa[]): boolean {
  const s = situacao(etapas);
  return s === "final" || s === "final_com_cache";
}

export function etapaAtual(etapas: Etapa[]): Etapa | null {
  return etapas.find((e) => e.estado === "rodando") ?? etapas.find((e) => e.estado === "pendente") ?? null;
}

export const TEXTO_SITUACAO: Record<Situacao, string> = {
  carregando: "Calculando… o que aparece abaixo ainda é parcial e não é o resultado.",
  final: "Resultado completo.",
  final_com_cache: "Resultado completo, mas parte dos dados veio do cache. Veja as datas.",
  bloqueado: "Não foi possível calcular: uma fonte obrigatória falhou e não há cópia guardada.",
};

/** Simulação local (sem rede) para a tela de exemplo. */
export function simular(cenario: "sucesso" | "degradado" | "falha", passo: number): Etapa[] {
  return ETAPAS_PROVISORIAS.map((e, i) => {
    let estado: EstadoEtapa = i < passo ? "ok" : i === passo ? "rodando" : "pendente";
    if (cenario === "degradado" && e.id === "clima" && i < passo) estado = "cache";
    if (cenario === "falha" && e.id === "clima" && i <= passo) estado = "falha";
    if (cenario === "falha" && i > 2 && i <= passo) estado = "pendente";
    return { ...e, estado };
  });
}

// ---------------------------------------------------------------- resposta real (contrato 1.1.0)

/** Etapas enquanto o pedido está no servidor: uma chamada só, então a etapa atual é "cálculo no servidor". */
export function etapasEmAndamento(fase: "enviando" | "calculando" | "montando"): Etapa[] {
  const ordem = ["enviando", "calculando", "montando"] as const;
  const i = ordem.indexOf(fase);
  return [
    { id: "enviando", rotulo: "Enviando a lavoura e as premissas", obrigatoria: true },
    { id: "calculando", rotulo: "Cálculo no servidor (clima NASA, ZARC, solo, custo e preço)", obrigatoria: true },
    { id: "montando", rotulo: "Montando o resultado", obrigatoria: true },
  ].map((e, k) => ({ ...e, estado: k < i ? "ok" : k === i ? "rodando" : "pendente" }));
}

const estadoSecao = (s?: { estado: string }): EstadoEtapa => (!s ? "pendente" : s.estado === "disponivel" ? "ok" : "falha");

/** O que cada parte da resposta real trouxe: fonte por fonte (com data do cache) e seção por seção. */
export function etapasDaResposta(r: RespostaContrato): Etapa[] {
  const etapas: Etapa[] = [];
  const vistas = new Set<string>();
  for (const f of r.fontes ?? []) {
    if (vistas.has(f.fonte)) continue;
    vistas.add(f.fonte);
    const estado: EstadoEtapa = f.estado === "ok" ? "ok" : f.estado;
    const detalhe = f.estado === "cache" ? `cópia guardada de ${f.obtido_em ?? "data desconhecida"}` : f.estado === "falha" ? "fonte fora do ar, sem cópia guardada" : undefined;
    etapas.push({ id: `fonte:${f.fonte}`, rotulo: f.fonte, obrigatoria: true, estado, detalhe });
  }
  for (const c of r.culturas ?? []) {
    const nome = NOME_CULTURA[c.cultura] ?? c.cultura;
    for (const [k, rot] of [["risco_hidrico", "risco hídrico"], ["economia", "margem"]] as const) {
      const s = c[k];
      if (!s) continue;
      // Grupo "não sei": risco e margem são calculados por grupo dentro da recomendação, não na seção da cultura.
      const porGrupo = s.estado === "indisponivel" && (s.avisos ?? []).some((a) => a.codigo === "grupo_nao_sei");
      if (porGrupo) {
        etapas.push({ id: `${c.cultura}:${k}`, rotulo: `${nome}: ${rot}`, obrigatoria: false, estado: estadoSecao(r.recomendacao),
                      detalhe: "por grupo, na recomendação" });
        continue;
      }
      etapas.push({ id: `${c.cultura}:${k}`, rotulo: `${nome}: ${rot}`, obrigatoria: s.obrigatoria ?? true, estado: estadoSecao(s), detalhe: s.erro?.mensagem });
    }
  }
  etapas.push({ id: "recomendacao", rotulo: "Recomendação (ordem das alternativas)", obrigatoria: true, estado: estadoSecao(r.recomendacao), detalhe: r.recomendacao.erro?.mensagem });
  for (const k of ["vegetacao", "umidade"] as const) {
    const c = r.contextos[k];
    if (c.estado === "nao_solicitado") continue;
    etapas.push({ id: k, rotulo: k === "vegetacao" ? "Vegetação (NDVI MODIS)" : "Umidade do solo (SMAP)", obrigatoria: false, estado: estadoSecao(c), detalhe: c.erro?.mensagem });
  }
  return etapas;
}

/** O backend decide se é final (estado_geral); a tela só repete, sem promover parcial a final. */
export const TEXTO_ESTADO_GERAL: Record<RespostaContrato["estado_geral"], { texto: string; tipo: "fonte" | "aviso" | "erro" }> = {
  final: { texto: "Resultado completo.", tipo: "fonte" },
  final_com_cache: { texto: "Resultado completo, mas parte dos dados veio de cópia guardada. Veja as datas abaixo.", tipo: "aviso" },
  incompleto: { texto: "Resultado PARCIAL: algumas partes não puderam ser calculadas. Não é o resultado final; veja o que faltou.", tipo: "aviso" },
  erro: { texto: "Resultado PARCIAL com erro: uma parte obrigatória não pôde ser calculada. Não é o resultado final; veja os erros e o que fazer.", tipo: "erro" },
};

/** Erro acionável: o que houve, de onde veio, se há cópia guardada (e de quando) e o que fazer. */
export function textoErro(e: ErroFonte): string {
  const cache = e.cache_obtido_em ? `usando cópia guardada de ${e.cache_obtido_em}` : "sem cópia guardada";
  return `${e.mensagem} Origem: ${e.origem}. ${cache[0].toUpperCase()}${cache.slice(1)}.${e.acao ? ` O que fazer: ${e.acao}` : ""}`;
}
