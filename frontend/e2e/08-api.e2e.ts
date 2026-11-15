// Checagens diretas da API do contrato. A captura de cada etapa é um quadro-resumo renderizado no navegador;
// as respostas completas ficam em docs/testes-e2e/evidencias/08-api/.
import type { Page } from "@playwright/test";
import { API, expect, test } from "./auditoria";

const PEDIDO = {
  versao_contrato: "1.2.0",
  area: { tipo: "ponto", lat: -17.785278, lon: -50.965, confirmada: true, codigo_ibge: "5218805" },
  data_colheita_soja: "2027-01-20", solo: { textura: "argilosa" }, grupo: "nao_sei", metodologia: "comparar_alternativas",
  premissas_editadas: [{ modulo: "economia", id: "preco_r_saca", unidade: "R$/saca de 60 kg", cultura: "sorgo_granifero_2a_safra",
                         valor_novo: 55, origem_informada: "Cooperativa de Rio Verde (teste)", data_informada: "2026-11-10" }],
  contextos: { vegetacao: true, umidade: true },
};
// Campos de texto (iguais a CAMPOS_TEXTO do backend): o resto da resposta tem de ser idêntico em PT e EN.
const TEXTO = new Set(["mensagem", "acao", "motivo", "motivos_indisponivel", "hipoteses", "descricao", "nota", "notas", "pergunta",
  "periodo", "qualidade", "localizacao", "fonte", "regra", "temporal", "espacial", "espacial_texto", "escala", "limitacao", "uso",
  "texto", "natureza", "consulta", "detalhes", "risco_historico_falha_severa", "idioma", "pedido"]);
const semTexto = (o: any): any => Array.isArray(o) ? o.map(semTexto)
  : o && typeof o === "object" ? Object.fromEntries(Object.entries(o).filter(([k]) => !TEXTO.has(k)).map(([k, v]) => [k, semTexto(v)])) : o;

async function quadro(page: Page, titulo: string, linhas: [string, string][]) {
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  await page.setContent(`<meta charset="utf-8"><body style="font:15px system-ui;margin:24px;max-width:1100px">
    <h2 style="color:#1f5132">TELLUS · API · ${esc(titulo)}</h2><table style="border-collapse:collapse;width:100%">
    ${linhas.map(([a, b]) => `<tr><td style="border:1px solid #ccc;padding:6px;font-weight:600;width:32%;vertical-align:top">${esc(a)}</td>
      <td style="border:1px solid #ccc;padding:6px;font-family:ui-monospace,monospace;white-space:pre-wrap">${esc(b)}</td></tr>`).join("")}</table>`);
}

test("Mesmo pedido em PT e EN dá os mesmos números, ordem e hash", async ({ page, request, aud }) => {
  const pt = await request.post(`${API}/api/contrato/calcular`, { data: PEDIDO, timeout: 240_000 });
  const en = await request.post(`${API}/api/contrato/calcular`, { data: { ...PEDIDO, idioma: "en" }, timeout: 240_000 });
  const a = await pt.json(), b = await en.json();
  const ea = aud.evidencia("resposta_pt.json", a), eb = aud.evidencia("resposta_en.json", b);
  const ordem = (r: any) => r.recomendacao.conteudo.alternativas.map((x: any) => `${x.cultura} ${x.grupo} d${x.decendio}`);
  await aud.verificar("As duas respostas com HTTP 200", "200 e 200", async () => { expect(pt.status()).toBe(200); expect(en.status()).toBe(200); },
    async () => `${pt.status()} e ${en.status()}`);
  await aud.verificar("Idioma declarado na resposta", "pt-BR e en", async () => { expect(a.idioma).toBe("pt-BR"); expect(b.idioma).toBe("en"); },
    async () => `${a.idioma} e ${b.idioma}`);
  await aud.verificar("Mesmo hash do pedido", a.versoes.hash_pedido, async () => expect(b.versoes.hash_pedido).toBe(a.versoes.hash_pedido),
    async () => b.versoes.hash_pedido);
  await aud.verificar("Mesma ordem de alternativas", ordem(a).slice(0, 3).join(" · ") + " …", async () => expect(ordem(b)).toEqual(ordem(a)),
    async () => ordem(b).slice(0, 3).join(" · ") + " …");
  await aud.verificar("Tudo o que não é texto é idêntico (números, códigos, estados)", "igual",
    async () => expect(semTexto(b)).toEqual(semTexto(a)));
  await aud.verificar("Nenhuma mensagem sem tradução no inglês", "0 ocorrências de \"(PT)\"",
    async () => expect(JSON.stringify(b)).not.toContain("(PT)"), async () => `${(JSON.stringify(b).match(/\(PT\)/g) ?? []).length} ocorrências`);
  await quadro(page, "PT × EN", [
    ["Estado geral", `${a.estado_geral} / ${b.estado_geral}`], ["Hash do pedido", `${a.versoes.hash_pedido} / ${b.versoes.hash_pedido}`],
    ["Alternativas (ordem)", ordem(a).join("\n")],
    ["Critério (PT)", a.recomendacao.conteudo.criterio_ordem.map((c: any) => c.descricao).join("; ")],
    ["Critério (EN)", b.recomendacao.conteudo.criterio_ordem.map((c: any) => c.descricao).join("; ")],
    ["Evidências", `${ea}\n${eb}`],
  ]);
  await aud.captura("pt e en com os mesmos numeros");
});

test("Versões do contrato: 1.1.0 aceita, 2.0.0 recusada com as versões aceitas", async ({ page, request, aud }) => {
  const v = await (await request.get(`${API}/api/contrato/versao`)).json();
  const antigo = await request.post(`${API}/api/contrato/pedido/validar`, { data: { ...PEDIDO, versao_contrato: "1.1.0" } });
  const novo = await request.post(`${API}/api/contrato/pedido/validar`, { data: { ...PEDIDO, versao_contrato: "2.0.0" } });
  const corpoNovo = await novo.json();
  aud.evidencia("versao.json", v); aud.evidencia("pedido_2.0.0.json", corpoNovo);
  await aud.verificar("Servidor fala o contrato 1.2.0", "1.2.0", async () => expect(v.versao_contrato).toBe("1.2.0"), async () => v.versao_contrato);
  await aud.verificar("Pedido 1.1.0 continua aceito", "HTTP 200", async () => expect(antigo.status()).toBe(200), async () => `HTTP ${antigo.status()}`);
  await aud.verificar("Pedido 2.0.0 recusado com código", "HTTP 422, versao_incompativel",
    async () => { expect(novo.status()).toBe(422); expect(corpoNovo.erro.codigo).toBe("versao_incompativel"); },
    async () => `HTTP ${novo.status()}, ${corpoNovo.erro?.codigo}`);
  await quadro(page, "versões", [["Versão do servidor", v.versao_contrato], ["Versões aceitas", v.versoes_aceitas.join(", ")],
    ["Pedido 1.1.0", `HTTP ${antigo.status()}`], ["Pedido 2.0.0", `HTTP ${novo.status()}\n${corpoNovo.erro?.mensagem}`]]);
  await aud.captura("versoes do contrato");
});

test("Pedido sem área confirmada não começa o cálculo", async ({ page, request, aud }) => {
  const r = await request.post(`${API}/api/contrato/calcular`, { data: { ...PEDIDO, area: { ...PEDIDO.area, confirmada: false } } });
  const c = await r.json();
  aud.evidencia("area_nao_confirmada.json", c);
  await aud.verificar("Recusado antes do cálculo", "HTTP 422, pedido_invalido, campo area",
    async () => { expect(r.status()).toBe(422); expect(c.erro.codigo).toBe("pedido_invalido"); expect(c.erro.mensagem).toContain("confirmada"); },
    async () => `HTTP ${r.status()}, ${c.erro?.codigo}: ${c.erro?.mensagem}`);
  await quadro(page, "área não confirmada", [["HTTP", String(r.status())], ["Erro", JSON.stringify(c.erro, null, 1)]]);
  await aud.captura("area nao confirmada recusada");
});
