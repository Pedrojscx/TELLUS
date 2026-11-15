// Padrões REAIS das premissas para a lavoura escolhida (substitui os valores de exemplo do editor).
// Preço (CEPEA), custo e produtividade (Conab) vêm de POST /api/economia/margem sem perda simulada;
// a água disponível vem de POST /api/solo/classificar (classe AD do ZARC). Falhou: o editor fica no exemplo.

import { API_URL } from "../api";
import { comIdioma } from "../i18n/cliente";
import type { EntradasComparacao, Proveniencia } from "./contrato-provisorio";
import type { LavouraConfirmada } from "./lavoura";

export type Padroes = Record<string, { padrao: number; proveniencia: Proveniencia }>;

/** Converte as respostas do backend nos padrões do editor (puro, testável). */
export function mapearPadroes(margemMilho: any, solo: any | null): Padroes {
  const out: Padroes = {};
  const pr = margemMilho?.premissas ?? {};
  if (pr.preco?.status === "fonte" && pr.preco.valor != null) {
    const f = pr.preco.fonte ?? {};
    out.preco_milho = { padrao: pr.preco.valor, proveniencia: {
      fonte: `${f.fonte} (${f.indicador}), ${f.praca}, cotação de ${f.data}`, url: f.url ?? null, obtido_em: f.obtido_em ?? null,
      unidade: pr.preco.unidade, situacao: "fonte", origem_dados: "fonte" } };
  }
  if (pr.custo?.status === "fonte" && pr.custo.valor_padrao_r_ha != null) {
    out.custo_milho = { padrao: Math.round(pr.custo.valor_padrao_r_ha), proveniencia: {
      fonte: `Conab, custo operacional por hectare (${pr.produtividade?.fonte?.planilha ?? "praça mais próxima"})`,
      unidade: "R$/ha", situacao: "fonte", origem_dados: "fonte" } };
  }
  if (pr.produtividade?.status === "fonte" && pr.produtividade.valor) {
    out.sacas_ha_milho = { padrao: Math.round((pr.produtividade.valor / 60) * 10) / 10, proveniencia: {
      fonte: `Conab, produtividade de referência ${pr.produtividade.fonte?.tipo ?? ""} (${pr.produtividade.fonte?.planilha ?? ""}); ${pr.produtividade.valor} kg/ha ÷ 60`,
      unidade: "sc/ha", situacao: "fonte", origem_dados: "fonte" } };
  }
  if (solo?.cad_mm != null) {
    out.cad_mm = { padrao: solo.cad_mm, proveniencia: {
      fonte: `Classe ${solo.classe ?? "?"} do ZARC (IN SPA/MAPA nº 1/2022 e portaria do milho)${solo.status === "hipotese" ? ", a partir da textura (granulometria típica, não medida)" : ""}`,
      unidade: "mm", situacao: solo.status === "hipotese" ? "hipotese" : "fonte", origem_dados: "fonte" } };
  }
  return out;
}

export async function carregarPadroes(lav: LavouraConfirmada, e: EntradasComparacao | undefined): Promise<Padroes> {
  const post = (rota: string, corpo: unknown) =>
    fetch(`${API_URL}${rota}`, comIdioma({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) }))
      .then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const textura = e?.solo && e.solo.modo !== "mm" ? e.solo.textura : null;
  const [margem, solo] = await Promise.all([
    post("/api/economia/margem", { lat: lav.lat, lon: lav.lon, cultura: "milho_2a_safra" }),
    textura ? post("/api/solo/classificar", { cultura: "milho_2a_safra", uf: lav.uf, textura }) : Promise.resolve(null),
  ]);
  return mapearPadroes(margem, solo);
}
