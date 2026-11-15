// Renderização da lista de referências do local (spec 001, US2).
import type { Aviso, Referencia, ResultadoLocalizacao } from "./api";

const TITULOS: Record<Referencia["tipo"], { titulo: string; uso: string }> = {
  celula_power: { titulo: "Clima (NASA POWER)", uso: "temperatura, radiação, umidade e vento" },
  celula_imerg: { titulo: "Chuva (NASA IMERG)", uso: "chuva diária por satélite" },
  estacao_inmet: { titulo: "Estação INMET", uso: "conferência local da chuva" },
  praca_conab: { titulo: "Custos (Conab)", uso: "custo de produção por hectare" },
  municipio_zarc: { titulo: "Município para o ZARC", uso: "janela oficial de plantio" },
};

const CULTURAS: Record<string, string> = {
  soja: "Soja",
  milho_2a_safra: "Milho 2ª safra",
  sorgo: "Sorgo",
};

export function esc(texto: unknown): string {
  return String(texto ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const km = (d: number) => `${d.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} km`;
const coord = (v: number) => v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 4 });

function detalhe(r: Referencia): string {
  const d = r.detalhes;
  if (r.tipo === "estacao_inmet" && d.altitude_m != null)
    return `${esc(r.identificador)} · altitude ${esc(Math.round(d.altitude_m))} m · ${esc(d.situacao)}`;
  if (r.tipo === "celula_power") return `centro da célula ${coord(r.lat)}; ${coord(r.lon)} (grade 0,5° × 0,625°)`;
  if (r.tipo === "celula_imerg") return `centro da célula ${coord(r.lat)}; ${coord(r.lon)} (grade 0,1°)`;
  if (r.tipo === "municipio_zarc") return `código IBGE ${esc(r.identificador)}`;
  if (r.tipo === "praca_conab" && d.mais_proxima_por_cultura) {
    const linhas = Object.entries(d.mais_proxima_por_cultura as Record<string, any>)
      .map(([c, p]) =>
        p ? `${esc(CULTURAS[c] ?? c)}: ${esc(p.nome)} (${km(p.distancia_km)})` : `${esc(CULTURAS[c] ?? c)}: sem praça`,
      )
      .join(" · ");
    return linhas;
  }
  return "";
}

function avisoHtml(a: Aviso): string {
  return `<li class="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">${esc(a.mensagem)}</li>`;
}

export function renderReferencias(res: ResultadoLocalizacao): string {
  const avisos = res.avisos.length
    ? `<ul class="mb-4 space-y-2" aria-label="Avisos">${res.avisos.map(avisoHtml).join("")}</ul>`
    : "";
  const itens = res.referencias
    .map((r) => {
      const t = TITULOS[r.tipo];
      const hip = r.procedencia.status === "hipotese" ? ` <span class="text-amber-700">(hipótese)</span>` : "";
      return `
      <li class="rounded-lg border border-stone-200 bg-white p-4">
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <h3 class="font-semibold text-stone-900">${esc(t.titulo)}</h3>
          <span class="text-sm tabular-nums text-stone-600">a ${km(r.distancia_km)}</span>
        </div>
        <p class="text-sm text-stone-500">${esc(t.uso)}</p>
        ${r.nome ? `<p class="mt-1 text-stone-800">${esc(r.nome)}</p>` : ""}
        <p class="mt-1 text-sm text-stone-700">${detalhe(r)}</p>
        <p class="mt-2 text-xs text-stone-500">Fonte: <a class="underline" href="${esc(r.procedencia.url)}" target="_blank" rel="noopener">${esc(r.procedencia.fonte)}</a> · obtido em ${esc(r.procedencia.obtido_em)}${hip}</p>
      </li>`;
    })
    .join("");
  return `${avisos}<ul class="grid gap-3 sm:grid-cols-2">${itens}</ul>
    <p class="mt-3 text-xs text-stone-500">Referências de ${esc(res.versao_referencias)}. Estimativas regionais; não representam o talhão.</p>`;
}
