// Validação local das entradas da 012 (#100). Funções puras, sem rede.
// Só a forma e o domínio que as specs já fixam são checados aqui:
//   - data exata (AAAA-MM-DD, dia que existe no calendário);
//   - solo: textura arenosa | média | argilosa (spec 005 FR-002) OU água disponível em mm (> 0);
//   - grupo I | II | III | "não sei" (spec 012 FR-002; spec 004 trata "não sei" como todos os grupos).
// Limites de faixa (datas aceitas, mm máximo) ficam EM ABERTO até a 005/011: não são inventados.

import type { EntradasComparacao, Grupo, Textura } from "./contrato-provisorio";

export interface ErroCampo {
  campo: "area" | "colheita_soja" | "solo" | "grupo" | "metodologia" | "cultura";
  mensagem: string;
}

const TEXTURAS: Textura[] = ["arenosa", "media", "argilosa"];
const GRUPOS: Grupo[] = ["I", "II", "III", "nao_sei"];

export function validarData(texto: string | null | undefined): string | null {
  if (!texto) return "Informe a data da colheita da soja.";
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto.trim());
  if (!m) return "Use a data completa no formato AAAA-MM-DD (ex.: 2026-02-10).";
  const [a, mes, dia] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const d = new Date(Date.UTC(a, mes - 1, dia));
  if (d.getUTCFullYear() !== a || d.getUTCMonth() !== mes - 1 || d.getUTCDate() !== dia) {
    return "Essa data não existe no calendário.";
  }
  return null;
}

/** Aceita "60", "60,5" ou "60.5" (espaços só nas pontas). Espaço interno ("6 0") é inválido. */
export function lerNumero(texto: string | null | undefined): number | string {
  if (texto == null || texto.trim() === "") return "Informe um número.";
  const limpo = texto.trim().replace(",", ".");
  if (!/^-?\d+(\.\d+)?$/.test(limpo)) return "Use só números (ex.: 60 ou 60,5).";
  return Number(limpo);
}

export function validarSolo(solo: EntradasComparacao["solo"]): string | null {
  if (!solo) return "Escolha a textura do solo ou informe a água disponível em mm.";
  if (solo.modo === "textura") return TEXTURAS.includes(solo.textura) ? null : "Textura inválida.";
  if (!Number.isFinite(solo.cad_mm) || solo.cad_mm <= 0) return "A água disponível precisa ser maior que zero (mm).";
  return null;
}

export function validarGrupo(g: string | null | undefined): string | null {
  return g && (GRUPOS as string[]).includes(g) ? null : "Escolha o grupo I, II, III ou “não sei”.";
}

/** Erros que impedem avançar para a metodologia (cenário de aceite 1). */
export function validarEntradas(e: EntradasComparacao): ErroCampo[] {
  const erros: ErroCampo[] = [];
  if (!e.area || !e.area.confirmada) erros.push({ campo: "area", mensagem: "Confirme a área da lavoura no mapa antes de seguir." });
  const d = validarData(e.colheita_soja);
  if (d) erros.push({ campo: "colheita_soja", mensagem: d });
  const s = validarSolo(e.solo);
  if (s) erros.push({ campo: "solo", mensagem: s });
  const g = validarGrupo(e.grupo);
  if (g) erros.push({ campo: "grupo", mensagem: g });
  return erros;
}

export function validarMetodologia(e: EntradasComparacao): ErroCampo[] {
  const erros = validarEntradas(e);
  if (e.metodologia !== "cultura_escolhida" && e.metodologia !== "comparar_alternativas") {
    erros.push({ campo: "metodologia", mensagem: "Escolha uma das duas formas de calcular." });
  } else if (e.metodologia === "cultura_escolhida" && !e.cultura) {
    erros.push({ campo: "cultura", mensagem: "Escolha a cultura que você quer avaliar." });
  }
  return erros;
}
