// Indicador de carga por etapas (#103). Puro.
// Regra: o resultado só é "final" quando TODAS as etapas obrigatórias terminaram (ok ou com
// cache). Qualquer etapa pendente, rodando ou com falha impede mostrar o resultado como final.
// Os nomes das etapas são provisórios; a lista real virá do contrato da 011.

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
