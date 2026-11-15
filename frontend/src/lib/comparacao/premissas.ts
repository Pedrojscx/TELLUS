// Edição de premissas (#102). Puro: valida unidade/domínio e mostra padrão × editado.
// Os limites de cada premissa vêm do dado (hoje da fixture de exemplo; depois da 005/007 via 011).

import type { Alternativa, CenarioMargem, CotacaoInformada, Premissa } from "./contrato-provisorio";
import { lerNumero, validarDataCotacao } from "./validacao";

export function aplicarEdicao(p: Premissa, texto: string): { premissa: Premissa; erro: string | null } {
  if (texto.trim() === "") return { premissa: { ...p, editado: null }, erro: null }; // volta ao padrão
  const v = lerNumero(texto);
  if (typeof v === "string") return { premissa: p, erro: v };
  if (v < p.minimo || v > p.maximo) {
    return { premissa: p, erro: `Fora da faixa aceita: de ${fmt(p.minimo)} a ${fmt(p.maximo)} ${p.unidade}.` };
  }
  return { premissa: { ...p, editado: v === p.padrao ? null : v }, erro: null };
}

/** Valor em uso: editado, senão padrão, senão (premissa sem padrão) a cotação informada; null = indisponível. */
export function valorEmUso(p: Premissa): number | null {
  if (p.exige_cotacao) return p.cotacao?.valor ?? null;
  return p.editado ?? p.padrao;
}

export function diferenca(p: Premissa): { absoluta: number; percentual: number | null } | null {
  if (p.editado == null || p.padrao == null) return null;
  return {
    absoluta: p.editado - p.padrao,
    percentual: p.padrao !== 0 ? ((p.editado - p.padrao) / Math.abs(p.padrao)) * 100 : null,
  };
}

export function editadas(ps: Premissa[]): Premissa[] {
  return ps.filter((p) => p.editado != null && p.padrao != null);
}

// ---------------------------------------------------------------- cotação informada pelo produtor (D-005)

export interface EntradaCotacao {
  valor: string;
  origem: string;
  data: string;
}

export type ErroCotacao = { campo: "valor" | "origem" | "data"; mensagem: string };

/** Valor (> 0 e na faixa da premissa), origem (não vazia) e data (válida, não futura): os três obrigatórios.
 * Tudo vazio = sem cotação (a margem fica indisponível), sem erro. */
export function validarCotacao(p: Premissa, e: EntradaCotacao, hoje: string): { cotacao: CotacaoInformada | null; erros: ErroCotacao[] } {
  const vazio = !e.valor.trim() && !e.origem.trim() && !e.data.trim();
  if (vazio) return { cotacao: null, erros: [] };
  const erros: ErroCotacao[] = [];
  const v = lerNumero(e.valor);
  if (typeof v === "string") erros.push({ campo: "valor", mensagem: e.valor.trim() ? v : "Informe o valor da cotação." });
  else if (v <= 0) erros.push({ campo: "valor", mensagem: "O valor precisa ser maior que zero." });
  else if (v < p.minimo || v > p.maximo) erros.push({ campo: "valor", mensagem: `Fora da faixa aceita: de ${fmt(p.minimo)} a ${fmt(p.maximo)} ${p.unidade}.` });
  const origem = e.origem.trim().replace(/\s+/g, " ");
  if (!origem) erros.push({ campo: "origem", mensagem: "Informe de onde veio a cotação (ex.: cooperativa X, Rio Verde)." });
  const ed = validarDataCotacao(e.data, hoje);
  if (ed) erros.push({ campo: "data", mensagem: ed });
  if (erros.length) return { cotacao: null, erros };
  return { cotacao: { valor: v as number, origem_informada: origem, data_informada: e.data.trim() }, erros: [] };
}

export const MOTIVO_SEM_COTACAO = "Margem indisponível: não há cotação oficial do sorgo (o CEPEA não cobre sorgo — D-005). Informe a sua cotação nas premissas.";

/** Margens da alternativa com a premissa de preço exigida. Sem cotação: todas null + motivo (nunca zero).
 * Com cotação: margem = sacas/ha × preço − custo R$/ha (mesma fórmula da 007), sobre a base de EXEMPLO da fixture. */
export function margensComCotacao(a: Alternativa, ps: Premissa[]): { cenarios: CenarioMargem[]; motivo: string | null; cotacao: CotacaoInformada | null } {
  if (!a.preco_premissa_id) return { cenarios: a.cenarios, motivo: a.margem_indisponivel ?? null, cotacao: null };
  const p = ps.find((x) => x.id === a.preco_premissa_id);
  const cot = p?.cotacao ?? null;
  if (!cot) return { cenarios: a.cenarios.map((c) => ({ ...c, margem_r_ha: null })), motivo: a.margem_indisponivel ?? MOTIVO_SEM_COTACAO, cotacao: null };
  const cenarios = a.cenarios.map((c) =>
    c.sacas_ha == null || c.custo_r_ha == null
      ? { ...c, margem_r_ha: null }
      : { ...c, margem_r_ha: Math.round(c.sacas_ha * cot.valor - c.custo_r_ha) });
  const incompleto = cenarios.some((c) => c.margem_r_ha == null);
  return { cenarios, motivo: incompleto ? "Margem indisponível em parte dos cenários: falta base de sacas ou custo." : null, cotacao: cot };
}

export function fmt(n: number, casas = 2): string {
  return n.toLocaleString("pt-BR", { maximumFractionDigits: casas });
}

/** Junta as premissas da fixture/contrato com as salvas na sessão (por id): premissas novas entram com o valor base;
 * só `editado` e `cotacao` vêm da sessão. Evita perder uma premissa nova numa sessão antiga. */
export function mesclarPremissas(base: Premissa[], salvas: Premissa[] | null | undefined): Premissa[] {
  const porId = new Map((salvas ?? []).map((p) => [p.id, p]));
  return base.map((p) => {
    const s = porId.get(p.id);
    return s ? { ...p, editado: p.exige_cotacao ? null : s.editado ?? null, cotacao: p.exige_cotacao ? s.cotacao ?? null : null } : p;
  });
}
