// Edição de premissas (#102). Puro: valida unidade/domínio e mostra padrão × editado.
// Os limites de cada premissa vêm do dado (hoje da fixture de exemplo; depois da 005/007 via 011).

import type { Premissa } from "./contrato-provisorio";
import { lerNumero } from "./validacao";

export function aplicarEdicao(p: Premissa, texto: string): { premissa: Premissa; erro: string | null } {
  if (texto.trim() === "") return { premissa: { ...p, editado: null }, erro: null }; // volta ao padrão
  const v = lerNumero(texto);
  if (typeof v === "string") return { premissa: p, erro: v };
  if (v < p.minimo || v > p.maximo) {
    return { premissa: p, erro: `Fora da faixa aceita: de ${fmt(p.minimo)} a ${fmt(p.maximo)} ${p.unidade}.` };
  }
  return { premissa: { ...p, editado: v === p.padrao ? null : v }, erro: null };
}

export function valorEmUso(p: Premissa): number {
  return p.editado ?? p.padrao;
}

export function diferenca(p: Premissa): { absoluta: number; percentual: number | null } | null {
  if (p.editado == null) return null;
  return {
    absoluta: p.editado - p.padrao,
    percentual: p.padrao !== 0 ? ((p.editado - p.padrao) / Math.abs(p.padrao)) * 100 : null,
  };
}

export function editadas(ps: Premissa[]): Premissa[] {
  return ps.filter((p) => p.editado != null);
}

export function fmt(n: number, casas = 2): string {
  return n.toLocaleString("pt-BR", { maximumFractionDigits: casas });
}
