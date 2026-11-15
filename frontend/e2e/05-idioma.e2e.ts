import { expect, test } from "./auditoria";
import { COLHEITA, esperarResultado } from "./fluxo";

const PALAVRAS_PT = /(?<![\w.\/-])(não|com|sem|para|safra|margem|decêndio|cultura|cópia|indisponível)(?![\w.\/-])/i;
const semLinks = (t: string) => t.replace(/https?:\/\/\S+/g, ""); // "github.com" não é a palavra "com"

test("Trocar para inglês no topo vale em todas as telas e no resultado real", async ({ page, aud }) => {
  await page.goto("/");
  await page.locator('[data-idioma="en"]').click();
  await aud.verificar("Página em inglês", "lang=en e \"Where is your field?\"",
    async () => { await expect(page.locator("html")).toHaveAttribute("lang", "en"); await expect(page.locator("#titulo-local")).toHaveText("Where is your field?"); });
  await aud.verificar("EN marcado no seletor", "aria-pressed=true no EN",
    () => expect(page.locator('[data-idioma="en"]')).toHaveAttribute("aria-pressed", "true"));
  await aud.captura("tela inicial em ingles");

  await page.locator("#busca").fill("Rio Verde");
  await page.locator("#sugestoes li[data-codigo]", { hasText: /^Rio Verde-GO$/ }).click();
  await expect(page.locator("#local-atual")).toContainText("Rio Verde-GO");
  await page.getByRole("link", { name: "Go to the comparison →" }).click();
  await aud.verificar("Idioma continua ao trocar de tela", "Entradas em inglês (\"Field data\")",
    () => expect(page.getByRole("heading", { level: 1, name: "Field data" })).toBeVisible());
  await page.locator("#usar-lavoura").click();
  await page.locator("#colheita").fill(COLHEITA);
  await page.locator('input[name="solo"][value="argilosa"]').check();
  await page.locator('input[name="grupo"][value="nao_sei"]').check();
  await aud.captura("entradas em ingles");
  await page.getByRole("button", { name: "Continue to method" }).click();
  await page.locator('input[name="metodologia"][value="comparar_alternativas"]').check();
  await aud.captura("metodologia em ingles");
  await page.getByRole("button", { name: "Calculate" }).click();
  await esperarResultado(page, aud);

  const real = page.locator("#resultado-real");
  await aud.verificar("Resultado real em inglês", "\"Options inside ZARC\" e critério em inglês",
    async () => { await expect(real).toContainText("Options inside ZARC"); await expect(real).toContainText("highest margin in the conservative scenario"); });
  await aud.verificar("Nenhuma mensagem do backend sem tradução", "nenhum \"(PT)\"",
    async () => expect(await real.innerText()).not.toContain("(PT)"));
  await aud.verificar("Sem palavras portuguesas no resultado visível", "nenhuma das palavras: não, com, sem, para, safra, margem…",
    async () => expect(semLinks(await real.innerText()).match(PALAVRAS_PT)).toBeNull(),
    async () => { const m = semLinks(await real.innerText()).match(PALAVRAS_PT); return m ? `encontrado: "${m[0]}"` : "nenhuma"; });
  const primeiro = real.locator("details.group").first();
  await primeiro.locator("summary").click();
  await aud.verificar("Riscos e cenários em inglês", "Official risk (ZARC), Conservative/Central/Favorable",
    async () => { await expect(primeiro).toContainText("Official risk (ZARC)"); await expect(primeiro.locator("table")).toContainText("Conservative"); });
  await aud.captura("resultado real em ingles");

  await page.locator('[data-idioma="pt-BR"]').click();
  await esperarResultado(page, aud);
  await aud.verificar("Voltar para PT recalcula em português", "lang=pt-BR e \"Alternativas dentro do ZARC\"",
    async () => { await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR"); await expect(page.locator("#resultado-real")).toContainText("Alternativas dentro do ZARC"); });
  await aud.captura("de volta ao portugues", { paginaInteira: false });
});

test("Link com ?lang=en abre direto em inglês", async ({ page, aud }) => {
  await page.goto("/comparacao/metodologia?lang=en");
  await aud.verificar("Metodologia em inglês pelo link", "\"How to calculate\"", () => expect(page.getByRole("heading", { level: 1, name: "How to calculate" })).toBeVisible());
  await aud.captura("link com lang en");
});
