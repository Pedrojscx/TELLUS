// Lavoura confirmada na tela inicial (spec 002/001) → comparação (012). Gancho de confirmação do plan.md.
// sessionStorage é conveniência: se falhar, a comparação volta para a área de exemplo identificada.

export interface LavouraConfirmada {
  tipo: "ponto" | "geometria";
  lat: number;
  lon: number;
  codigo_ibge: string | null;
  municipio: string;
  uf: string;
  area_ha: number | null; // ponto não tem área
  geometria?: Record<string, unknown>;
  id_geometria?: string;
  origem?: "car" | "upload_sicar" | "desenho" | "arquivo";
  confirmada_em: string;
}

const CHAVE = "tellus.lavoura.v1";

export function salvarLavoura(l: LavouraConfirmada): void {
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(l));
  } catch {
    /* sem armazenamento */
  }
}

export function lerLavoura(): LavouraConfirmada | null {
  try {
    const t = sessionStorage.getItem(CHAVE);
    return t ? (JSON.parse(t) as LavouraConfirmada) : null;
  } catch {
    return null;
  }
}
