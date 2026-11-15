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
  area: { id_geometria: string; area_ha: number; municipio: string; uf: string; confirmada: boolean } | null;
  colheita_soja: string | null; // AAAA-MM-DD
  solo: { modo: "textura"; textura: Textura } | { modo: "mm"; cad_mm: number } | null;
  grupo: Grupo | null;
  metodologia: Metodologia | null;
  cultura?: string | null; // só na metodologia "cultura_escolhida"
}

export interface Premissa {
  id: string;
  nome: string;
  tipo: "solo" | "economica" | "cultura";
  padrao: number;
  editado?: number | null;
  unidade: string;
  minimo: number;
  maximo: number;
  proveniencia: Proveniencia;
}

export interface CenarioMargem {
  cenario: "conservador" | "central" | "favoravel";
  margem_r_ha: number;
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
