import type { Page } from "@playwright/test";
import { expect, test } from "./auditoria";
import { calcular, escolherRioVerde, preencherEntradas } from "./fluxo";

test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });

const larguras = (page: Page) => page.evaluate(() => ({ pagina: document.documentElement.scrollWidth, tela: window.innerWidth }));
const semRolagemLateral = async (page: Page) => {
  const l = await larguras(page);
  expect(l.pagina).toBeLessThanOrEqual(l.tela + 1);
  return `${l.pagina}px de conteúdo em ${l.tela}px de tela`;
};

test("Fluxo completo no celular sem nada cortado na lateral", async ({ page, aud }) => {
  await page.goto("/");
  await aud.verificar("Tela inicial cabe na largura", "sem rolagem lateral", () => semRolagemLateral(page));
  await aud.captura("tela inicial no celular");

  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await aud.verificar("Metodologia cabe na largura", "sem rolagem lateral", () => semRolagemLateral(page));
  await aud.verificar("Menu de etapas quebra linha", "menu inteiro dentro da tela",
    async () => { const b = await page.getByRole("navigation").first().boundingBox(); expect(b!.x + b!.width).toBeLessThanOrEqual(391); });
  await aud.captura("metodologia no celular");

  await calcular(page, aud);
  await aud.verificar("Resultado cabe na largura", "sem rolagem lateral", () => semRolagemLateral(page));
  await page.locator("#resultado-real details.group").first().locator("summary").tap();
  await aud.verificar("Alternativa abre com toque", "riscos visíveis",
    () => expect(page.locator("#resultado-real details.group").first()).toContainText("Risco oficial (ZARC)"));
  await aud.captura("resultado no celular");
});
