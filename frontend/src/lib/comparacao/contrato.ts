// Adaptador REAL do contrato 1.1.0 (spec 011 #54 → 012). Substitui `carregarExemplo` quando há lavoura confirmada.
// Monta o pedido, chama POST /api/contrato/calcular e converte a resposta para os tipos que as telas já usam
// (contrato-provisorio.ts). Os tipos de resposta abaixo cobrem só os campos lidos aqui.

import { API_URL } from "../api";
import {
  premissasParaPedido,
  type Alternativa, type Aviso, type ContextoOpcional, type EntradasComparacao, type ErroFonte,
  type Premissa, type Proveniencia, type ResultadoComparacao,
} from "./contrato-provisorio";
import type { LavouraConfirmada } from "./lavoura";

export const VERSAO_CONTRATO = "1.1.0";

export const NOME_CULTURA: Record<string, string> = {
  milho_2a_safra: "Milho 2ª safra",
  sorgo_granifero_2a_safra: "Sorgo granífero 2ª safra",
  braquiaria_cobertura: "Braquiária (cobertura)",
};

const GRUPO: Record<string, string> = { I: "GRUPO I", II: "GRUPO II", III: "GRUPO III", nao_sei: "nao_sei" };

// ---------------------------------------------------------------- pedido

export interface FalhaPedido {
  codigo: string;
  mensagem: string;
  campo?: string | null;
}

export function montarPedido(e: EntradasComparacao, lavoura: LavouraConfirmada, premissas: Premissa[]): Record<string, unknown> {
  const area =
    lavoura.tipo === "geometria" && lavoura.geometria && lavoura.id_geometria
      ? { tipo: "geometria", geometria: lavoura.geometria, id_geometria: lavoura.id_geometria, origem: lavoura.origem ?? "desenho", confirmada: true }
      : { tipo: "ponto", lat: lavoura.lat, lon: lavoura.lon, confirmada: true, ...(lavoura.codigo_ibge ? { codigo_ibge: lavoura.codigo_ibge } : {}) };
  // A água disponível editada nas premissas prevalece sobre a escolha das Entradas (o produtor informou o valor).
  const cadEditado = premissas.find((p) => p.id === "cad_mm" && p.editado != null)?.editado ?? null;
  const solo = cadEditado != null ? { cad_mm: cadEditado }
    : e.solo?.modo === "mm" ? { cad_mm: e.solo.cad_mm } : e.solo ? { textura: e.solo.textura } : {};
  const pedido: Record<string, unknown> = {
    versao_contrato: VERSAO_CONTRATO,
    area,
    data_colheita_soja: e.colheita_soja,
    solo,
    grupo: GRUPO[e.grupo ?? "nao_sei"],
    metodologia: e.metodologia ?? "comparar_alternativas",
    premissas_editadas: premissasParaPedido(premissas),
    contextos: { vegetacao: true, umidade: true },
  };
  if (e.metodologia === "cultura_escolhida" && e.cultura) pedido.cultura = e.cultura;
  return pedido;
}

export async function calcular(pedido: Record<string, unknown>): Promise<RespostaContrato> {
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}/api/contrato/calcular`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pedido),
    });
  } catch {
    throw { codigo: "sem_conexao", mensagem: "Não foi possível falar com o servidor do TELLUS. Ele está rodando?" } as FalhaPedido;
  }
  const corpo = await resp.json();
  if (!resp.ok) throw (corpo.erro ?? { codigo: "erro", mensagem: "Erro inesperado no cálculo." }) as FalhaPedido;
  return corpo as RespostaContrato;
}

// ---------------------------------------------------------------- resposta (campos lidos)

interface ProvContrato {
  id: string; fonte: string; versao: string; periodo: string; unidade: string; localizacao: string; qualidade: string;
  situacao: string; url?: string | null; obtido_em?: string | null;
}
interface AvisoContrato { codigo: string; mensagem: string; origem?: string }
interface ErroContrato { codigo: string; mensagem: string; origem: string; cache?: { obtido_em?: string | null }; acao?: string | null }
interface AlternativaContrato {
  cultura: string; grupo: string; decendio: number; data_plantio: string; risco_zarc_pct: number | null; portaria_zarc: string | null;
  risco_historico_falha_severa: number | null; anos_validos: number; deficit_mm_mediano: number | null;
  margem_r_ha: Record<"conservador" | "central" | "favoravel", number | null>; hipoteses: string[]; posicao: number;
  versoes: { motor: string; economia: string };
}
interface Secao { estado: string; conteudo: any; proveniencia: ProvContrato[]; avisos: AvisoContrato[]; erro: ErroContrato | null }
export interface RespostaContrato {
  versao_contrato: string; estado_geral: "final" | "final_com_cache" | "incompleto" | "erro"; final: boolean;
  recomendacao: Secao;
  contextos: Record<"vegetacao" | "umidade", { estado: string; conteudo: any; avisos: AvisoContrato[]; erro: ErroContrato | null }>;
  avisos: AvisoContrato[]; erros: ErroContrato[]; hipoteses: string[];
  premissas_editadas?: { modulo: string; id: string; valor_novo: number; unidade: string; cultura: string | null;
                         valor_padrao: number | null; origem_informada?: string | null; data_informada?: string | null }[];
  fontes?: { fonte: string; estado: "ok" | "cache" | "falha"; obtido_em: string | null; secao: string }[];
  culturas?: ({ cultura: string } & Partial<Record<"risco_hidrico" | "economia", { estado: string; obrigatoria?: boolean; erro: ErroContrato | null }>>)[];
}

const num = (v: number) => v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });

/** "Preço (milho): padrão 67,34 → 70 R$/saca (produtor)": padrão e edição lado a lado, com a origem (#102). */
export function textoAlteracao(p: NonNullable<RespostaContrato["premissas_editadas"]>[number]): string {
  const cult = p.cultura ? ` (${NOME_CULTURA[p.cultura] ?? p.cultura})` : "";
  const padrao = p.valor_padrao == null ? "sem padrão com fonte" : `padrão ${num(p.valor_padrao)}`;
  const origem = p.origem_informada ? `informado: ${p.origem_informada}, ${p.data_informada}` : "editado pelo produtor";
  return `${p.id}${cult}: ${padrao} → ${num(p.valor_novo)} ${p.unidade} (${origem})`;
}

function situacao(s: string): Proveniencia["situacao"] {
  if (s === "fonte" || s === "cache" || s === "calculado" || s === "pedido") return "fonte";
  if (s === "hipotese") return "hipotese";
  if (s === "editado" || s === "informada_pelo_produtor") return "editado";
  return "desconhecido";
}

export function paraProveniencia(p: ProvContrato): Proveniencia {
  return {
    fonte: p.fonte, versao: p.versao, unidade: p.unidade, escala: p.localizacao,
    qualidade: `${p.qualidade}${p.periodo ? ` · período ${p.periodo}` : ""}`,
    obtido_em: p.obtido_em ?? null, url: p.url ?? null, situacao: situacao(p.situacao),
    origem_dados: p.situacao === "cache" ? "cache" : "fonte",
  };
}

function paraErro(e: ErroContrato): ErroFonte {
  return { codigo: e.codigo, mensagem: e.mensagem, origem: e.origem, cache_obtido_em: e.cache?.obtido_em ?? null, acao: e.acao ?? null };
}

const plantio = (mmdd: string) => mmdd.split("-").reverse().join("/");

export function paraAlternativa(a: AlternativaContrato, provs: Proveniencia[]): Alternativa {
  return {
    cultura: NOME_CULTURA[a.cultura] ?? a.cultura,
    grupo: a.grupo.replace("GRUPO ", ""),
    decendio: `decêndio ${a.decendio} (plantio ${plantio(a.data_plantio)})`,
    risco_zarc_pct: a.risco_zarc_pct ?? 0,
    risco_historico_falta_agua_pct: a.risco_historico_falha_severa == null ? 0 : Math.round(a.risco_historico_falha_severa * 1000) / 10,
    cenarios: (["conservador", "central", "favoravel"] as const).map((c) => ({ cenario: c, margem_r_ha: a.margem_r_ha[c] })),
    premissas_usadas: a.hipoteses,
    avisos: [],
    proveniencia: provs,
    preco_premissa_id: null, // margem já vem do backend (com a cotação informada, quando houver)
    margem_indisponivel: null,
  };
}

/** Situação de cada produto do contexto (ex.: MODIS com 23 composições; HLS indisponível com o motivo). */
export function produtos(conteudo: any): string[] {
  return ((conteudo?.fontes ?? []) as any[]).map((f) => f.estado === "disponivel"
    ? `${f.produto}: disponível (${(f.serie ?? []).length} composições).`
    : `${f.produto}: indisponível${f.motivo?.mensagem ? ` (${f.motivo.mensagem})` : ""}.`);
}

function paraContexto(id: "vegetacao" | "umidade", c: RespostaContrato["contextos"]["vegetacao"]): ContextoOpcional {
  const titulo = id === "vegetacao" ? "Vegetação (MODIS e HLS, contexto histórico)" : "Umidade do solo (SMAP)";
  const avisos = c.avisos ?? [];
  const escala = avisos.find((a) => /escala|regional|km/i.test(a.codigo + a.mensagem));
  const base = c.estado === "disponivel" ? (avisos.find((a) => a !== escala)?.mensagem ?? "Série disponível; não entra no cálculo.")
    : c.estado === "nao_solicitado" ? "Não solicitado." : "Indisponível nesta consulta.";
  return {
    id, titulo, disponivel: c.estado === "disponivel",
    resumo: [base, ...produtos(c.conteudo)].join(" "),
    aviso_escala: escala?.mensagem ?? "Produto de escala regional: não representa a lavoura.",
    proveniencia: null,
    erro: c.erro ? paraErro(c.erro) : null,
  };
}

export function paraResultado(r: RespostaContrato, metodologia: "cultura_escolhida" | "comparar_alternativas"): ResultadoComparacao {
  const rec = r.recomendacao;
  const provs = (rec.proveniencia ?? []).map(paraProveniencia);
  const alts: AlternativaContrato[] = rec.conteudo?.alternativas ?? [];
  const criterio = (rec.conteudo?.criterio_ordem ?? []).map((c: { descricao: string }) => c.descricao).join("; ");
  const indisponiveis: Aviso[] = (rec.conteudo?.indisponiveis ?? []).map((i: any) => ({
    codigo: "fora_da_recomendacao",
    mensagem: `${NOME_CULTURA[i.cultura] ?? i.cultura}${i.grupo ? `, ${i.grupo}` : ""}${i.decendio ? `, decêndio ${i.decendio}` : ""}: ${i.motivo}`,
  }));
  return {
    exemplo: false,
    versao_contrato: r.versao_contrato,
    metodologia,
    criterio_ordem: criterio || "—",
    alternativas: alts.map((a) => {
      const alt = paraAlternativa(a, provs);
      const mudancas = (r.premissas_editadas ?? []).filter((p) => p.cultura == null || p.cultura === a.cultura).map(textoAlteracao);
      return { ...alt, premissas_usadas: [...mudancas, ...alt.premissas_usadas] };
    }),
    avisos: [...(r.avisos ?? []), ...(rec.avisos ?? []), ...indisponiveis].map((a) => ({ codigo: a.codigo, mensagem: a.mensagem })),
    erros: (r.erros ?? []).map(paraErro),
    contextos_opcionais: (["vegetacao", "umidade"] as const).map((k) => paraContexto(k, r.contextos[k])),
  };
}
