import { expect, test } from "./auditoria";
import { escolherRioVerde } from "./fluxo";

test("Tela inicial abre com marca, passo a passo e seletor de local", async ({ page, aud }) => {
  await page.goto("/");
  await aud.verificar("Título da aba", "TELLUS · segunda safra", () => expect(page).toHaveTitle("TELLUS · segunda safra"), () => page.title());
  await aud.verificar("Ícone próprio do TELLUS na aba", "/favicon.svg", async () => {
    const href = await page.locator('link[rel="icon"]').getAttribute("href");
    expect(href).toContain("/favicon.svg");
    return href ?? "";
  });
  await aud.verificar("Passo a passo de 4 etapas", "4 itens em \"Como usar\"",
    () => expect(page.getByRole("list", { name: "Como usar" }).locator("li")).toHaveCount(4),
    () => page.getByRole("list", { name: "Como usar" }).innerText());
  await aud.verificar("Sem faixa de dado de exemplo na tela inicial", "nenhum \"DADO DE EXEMPLO\"",
    () => expect(page.getByText("DADO DE EXEMPLO")).toHaveCount(0));
  await aud.verificar("Seletor de idioma no topo", "botões PT e EN, PT marcado",
    () => expect(page.locator('[data-idioma="pt-BR"]')).toHaveAttribute("aria-pressed", "true"));
  await aud.captura("tela inicial");
});

test("Escolher Rio Verde-GO pela busca mostra as fontes do local", async ({ page, aud }) => {
  await escolherRioVerde(page, aud);
  const refs = page.getByText("De onde vêm os dados deste local").locator("xpath=ancestor::section[1]");
  for (const fonte of ["NASA POWER", "IMERG", "INMET", "Conab", "ZARC"]) {
    await aud.verificar(`Fonte "${fonte}" listada com distância`, fonte, () => expect(refs).toContainText(fonte));
  }
  await refs.scrollIntoViewIfNeeded();
  await aud.captura("fontes do local escolhido");
});

test("Coordenadas digitadas também escolhem o local", async ({ page, aud }) => {
  await page.goto("/");
  await page.locator("#lat").fill("-17.785");
  await page.locator("#lon").fill("-50.965");
  await aud.captura("coordenadas digitadas", { paginaInteira: false });
  await page.getByRole("button", { name: "Usar" }).click();
  await aud.verificar("Coordenadas de Rio Verde resolvem o município", "Rio Verde-GO",
    () => expect(page.locator("#local-atual")).toContainText("Rio Verde-GO"), () => page.locator("#local-atual").innerText());
  await aud.captura("local pelas coordenadas", { paginaInteira: false });
});

test("Coordenada fora do Brasil é recusada com mensagem em português", async ({ page, aud }) => {
  await page.goto("/");
  await page.locator("#lat").fill("40.0");
  await page.locator("#lon").fill("-3.7");
  await page.getByRole("button", { name: "Usar" }).click();
  await aud.verificar("Erro legível para ponto fora do território", "mensagem de erro visível",
    () => expect(page.locator("#erro-local")).toBeVisible(), () => page.locator("#erro-local").innerText());
  await aud.captura("ponto fora do Brasil recusado", { paginaInteira: false });
});

test("Botão da tela inicial leva à comparação", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await page.getByRole("link", { name: "Seguir para a comparação →" }).click();
  await aud.verificar("Link abre as Entradas", "URL /comparacao/entradas",
    () => expect(page).toHaveURL(/\/comparacao\/entradas/), async () => page.url());
  await aud.verificar("Lavoura escolhida oferecida nas Entradas", "botão \"Usar a lavoura confirmada (Rio Verde-GO, ponto)\"",
    () => expect(page.locator("#usar-lavoura")).toHaveText(/Rio Verde-GO/), () => page.locator("#usar-lavoura").innerText());
  await aud.captura("entradas com a lavoura escolhida");
});
