// Sessão de comparação no navegador (#100: preservar entradas confirmadas).
// sessionStorage é só conveniência: pode falhar (modo privado) e a tela segue funcionando.

import type { EntradasComparacao, Premissa } from "./contrato-provisorio";

const CHAVE = "tellus.comparacao.exemplo.v0";

export interface Sessao {
  exemplo: true;
  entradas: EntradasComparacao;
  premissas?: Premissa[];
}

export const VAZIA: EntradasComparacao = {
  area: null, colheita_soja: null, solo: null, grupo: null, metodologia: null, cultura: null,
};

export function ler(): Sessao | null {
  try {
    const t = sessionStorage.getItem(CHAVE);
    return t ? (JSON.parse(t) as Sessao) : null;
  } catch {
    return null;
  }
}

export function gravar(s: Sessao): void {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(s));
  } catch {
    /* sem armazenamento: a sessão vive só na página */
  }
}

export function limpar(): void {
  try {
    sessionStorage.removeItem(CHAVE);
  } catch {
    /* idem */
  }
}
