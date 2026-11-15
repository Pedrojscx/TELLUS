// Tradução PT → EN de um texto da tela (spec 014). Puro e testável; o DOM fica em cliente.ts.
// Ordem: frase inteira do dicionário; senão trechos conhecidos (palavra inteira); depois números e datas no formato
// do inglês. Os valores não mudam, só a escrita: 5.889,09 → 5,889.09; 20/01/2027 → Jan 20, 2027.

import { FRASES, TRECHOS } from "./en";

export type Idioma = "pt-BR" | "en";

const MESES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const TRECHOS_RE = [...TRECHOS]
  .sort((a, b) => b[0].length - a[0].length)
  .map(([pt, en]) => [new RegExp(`(?<![\\p{L}\\d])${esc(pt)}(?![\\p{L}\\d])`, "gu"), en] as const);

/** 5.889,09 → 5,889.09 ; 67,34 → 67.34 ; 10.000 → 10,000. Não mexe em 1.1.0 nem em datas ISO. */
export function numerosEn(s: string): string {
  return s.replace(/(?<![\d.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\d.]*\d)|(?<![\d.,])\d+,\d+(?![\d,]*\d)/g, (m) =>
    m.replace(/\./g, "\u0000").replace(/,/g, ".").replace(/\u0000/g, ","));
}

/** 20/01/2027 → Jan 20, 2027 ; 10/02 → Feb 10. Só com dia e mês válidos. */
export function datasEn(s: string): string {
  return s.replace(/(?<![\d/])(\d{2})\/(\d{2})(?:\/(\d{4}))?(?![\d/])/g, (m, d, mes, ano) => {
    const i = Number(mes) - 1, dia = Number(d);
    if (i < 0 || i > 11 || dia < 1 || dia > 31) return m;
    return `${MESES[i]} ${dia}${ano ? `, ${ano}` : ""}`;
  });
}

/** Traduz um texto (já sem espaços nas pontas). Retorna o próprio texto quando não há o que traduzir. */
export function traduzirTexto(texto: string): string {
  const norm = texto.replace(/\s+/g, " ").trim();
  if (!norm) return texto;
  const frase = FRASES[norm];
  if (frase != null) return frase; // já escrita em inglês, números inclusive
  let out = datasEn(numerosEn(norm));
  for (const [re, en] of TRECHOS_RE) out = out.replace(re, en);
  return out;
}

/** Preserva os espaços das pontas do nó de texto original. */
export function traduzirNo(texto: string): string {
  const ini = texto.match(/^\s*/)![0], fim = texto.match(/\s*$/)![0];
  const t = traduzirTexto(texto);
  return t === texto ? texto : `${ini}${t.trim()}${fim}`;
}
