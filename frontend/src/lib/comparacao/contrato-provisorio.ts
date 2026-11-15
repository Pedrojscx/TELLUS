// PROVISÓRIO até a spec 011 (#54).
//
// Único ponto que conhece o formato dos dados de comparação. As telas e os componentes de
// `components/comparacao/` importam só estes tipos e funções. Quando o contrato versionado da
// 011 existir, a troca acontece aqui: os tipos passam a vir do contrato e `carregarExemplo` vira a
// chamada real. Nada aqui chama endpoint: a API de cálculo (008/011) ainda não existe.
//
// Os nomes seguem as specs 004, 005, 007, 008, 010 e 011 e o que a API já devolve (proveniência,
// avisos, erro {codigo, mensagem, origem}). Eles NÃO são o contrato definitivo.

import exemplo from "../../fixtures/comparacao/rio-verde-exemplo.json";

/** Interruptor único: virar true quando a 008 com repasse da cotação informada estiver na main;
 * aí a margem vem do backend e o recálculo local (simulação de exemplo) sai. */
export const MARGEM_DO_BACKEND_DISPONIVEL = false;

export type Situacao = "fonte" | "hipotese" | "editado" | "desconhecido";

/** Bloco genérico de proveniência (FR-005 da 012; Princípio I). */
export interface Proveniencia {
  fonte: string;
  versao?: string | null;
  unidade?: string | null;
  escala?: string | null; // resolução espacial/temporal ou "praça a N km"
  qualidade?: string | null;
  obtido_em?: string | null; // data do dado ou do cache
  origem_dados?: "fonte" | "cache" | "referencia_versionada" | "exemplo";
  url?: string | null;
  situacao: Situacao;
}

export interface Aviso {
  codigo: string;
  mensagem: string;
}

/** Erro por fonte (spec 011 FR-004). Cache presente = degradado; ausente = falha. */
export interface ErroFonte {
  codigo: string;
  mensagem: string;
  origem: string;
  cache_obtido_em?: string | null;
  acao?: string | null;
}

export type Textura = "arenosa" | "media" | "argilosa";
export type Grupo = "I" | "II" | "III" | "nao_sei";
export type Metodologia = "cultura_escolhida" | "comparar_alternativas";

/** Entradas que a 012 coleta (FR-002). O formato final do pedido é da 011 (#96). */
export interface EntradasComparacao {
  /** `real: true` = lavoura confirmada na tela inicial (lavoura.ts); sem ela, é a área de exemplo identificada. */
  area: { id_geometria: string; area_ha: number; municipio: string; uf: string; confirmada: boolean; real?: boolean } | null;
  colheita_soja: string | null; // AAAA-MM-DD
  solo: { modo: "textura"; textura: Textura } | { modo: "mm"; cad_mm: number } | null;
  grupo: Grupo | null;
  metodologia: Metodologia | null;
  cultura?: string | null; // só na metodologia "cultura_escolhida"
}

/** Cotação informada pelo produtor (ex.: preço do sorgo, sem indicador oficial — D-005). */
export interface CotacaoInformada {
  valor: number;
  origem_informada: string; // texto livre, ex.: "cooperativa X, Rio Verde"
  data_informada: string; // AAAA-MM-DD
}

export interface Premissa {
  id: string;
  nome: string;
  tipo: "solo" | "economica" | "cultura";
  /** null = não há valor padrão com fonte (nunca se inventa um); só vale o informado pelo produtor. */
  padrao: number | null;
  editado?: number | null;
  unidade: string;
  minimo: number;
  maximo: number;
  proveniencia: Proveniencia;
  /** Premissa que só entra com valor, origem e data informados (ex.: preço do sorgo). */
  exige_cotacao?: boolean;
  sem_padrao_motivo?: string | null;
  cotacao?: CotacaoInformada | null;
  /** Mapeamento para o pedido da 011: módulo, id e cultura da premissa no backend. */
  pedido?: { modulo: "economia" | "culturas" | "motor"; id: string; cultura?: string | null };
}

export interface CenarioMargem {
  cenario: "conservador" | "central" | "favoravel";
  /** null = margem indisponível (nunca vira zero); o motivo fica em Alternativa.margem_indisponivel. */
  margem_r_ha: number | null;
  /** Base de EXEMPLO para recompor a margem quando o preço vem do produtor: sacas/ha e custo R$/ha. */
  sacas_ha?: number;
  custo_r_ha?: number;
}

export interface Alternativa {
  cultura: string;
  grupo: string;
  decendio: string;
  risco_zarc_pct: number;
  risco_historico_falta_agua_pct: number;
  cenarios: CenarioMargem[];
  premissas_usadas: string[];
  avisos: Aviso[];
  proveniencia: Proveniencia[];
  /** Premissa de preço exigida (ex.: "preco_sorgo"); sem ela a margem fica indisponível. */
  preco_premissa_id?: string | null;
  margem_indisponivel?: string | null;
}

export interface ContextoOpcional {
  id: "vegetacao" | "umidade";
  titulo: string;
  disponivel: boolean;
  resumo: string;
  aviso_escala: string;
  proveniencia: Proveniencia | null;
  erro?: ErroFonte | null;
}

export interface ResultadoComparacao {
  exemplo: boolean;
  versao_contrato: string;
  metodologia: Metodologia;
  criterio_ordem: string;
  alternativas: Alternativa[];
  avisos: Aviso[];
  erros: ErroFonte[];
  contextos_opcionais: ContextoOpcional[];
}

export interface DadosExemplo {
  exemplo: true;
  descricao: string;
  entradas: EntradasComparacao;
  premissas: Premissa[];
  resultado: ResultadoComparacao;
  estados_fonte: { sucesso: Proveniencia[]; degradado: ErroFonte[]; falha: ErroFonte[] };
}

/** Dados de exemplo identificados. Troque por chamada real quando a 011 existir. */
export function carregarExemplo(): DadosExemplo {
  const d = exemplo as unknown as DadosExemplo;
  if (d.exemplo !== true || d.resultado.exemplo !== true) {
    throw new Error("fixture sem a marca exemplo: true");
  }
  return d;
}

export const ROTULO_TEXTURA: Record<Textura, string> = { arenosa: "Arenosa", media: "Média", argilosa: "Argilosa" };
export const ROTULO_GRUPO: Record<Grupo, string> = { I: "Grupo I", II: "Grupo II", III: "Grupo III", nao_sei: "Não sei" };
export const ROTULO_CENARIO: Record<CenarioMargem["cenario"], string> = {
  conservador: "Conservador", central: "Central", favoravel: "Favorável",
};

/** Item de `premissas_editadas` do pedido. `origem_informada`/`data_informada` NÃO existem no contrato 1.0.0:
 * ficam aqui até a mudança proposta (MENOR 1.1.0, campos opcionais e compatíveis) — ver specs/012-interface-web/plan.md. */
export interface PremissaEditadaPedido {
  modulo: "economia" | "culturas" | "motor";
  id: string;
  valor_novo: number;
  unidade: string;
  cultura?: string | null;
  origem_informada?: string;
  data_informada?: string;
}

/** Premissas editadas/informadas → `pedido.premissas_editadas` (só as que têm mapeamento para o backend). */
export function premissasParaPedido(ps: Premissa[]): PremissaEditadaPedido[] {
  const saida: PremissaEditadaPedido[] = [];
  for (const p of ps) {
    if (!p.pedido) continue;
    const base = { modulo: p.pedido.modulo, id: p.pedido.id, unidade: p.unidade, cultura: p.pedido.cultura ?? null };
    if (p.exige_cotacao) {
      if (p.cotacao) saida.push({ ...base, valor_novo: p.cotacao.valor, origem_informada: p.cotacao.origem_informada, data_informada: p.cotacao.data_informada });
    } else if (p.editado != null) {
      saida.push({ ...base, valor_novo: p.editado });
    }
  }
  return saida;
}
