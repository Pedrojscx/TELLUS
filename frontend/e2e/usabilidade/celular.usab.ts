// Roteiro, passo 7: repetir os passos 1 a 4 no celular (390 × 844, toque).
import type { Page } from "@playwright/test";
import { expect, test } from "../auditoria";
import { Humano } from "./humano";

async function semCorteLateral(page: Page): Promise<string> {
  const l = await page.evaluate(() => ({ conteudo: document.documentElement.scrollWidth, tela: window.innerWidth }));
  expect(l.conteudo).toBeLessThanOrEqual(l.tela + 1);
  return `${l.conteudo}px de conteúdo em ${l.tela}px de tela`;
}

test("Passo 7: passos 1 a 4 no celular, com o dedo", async ({ page, aud }) => {
  const eu = new Humano(page, true);
  await page.goto("/");
  await eu.ler(1200);
  await aud.verificar("Passo 7 ✔ Tela inicial: nada cortado na lateral", "sem rolagem lateral", () => semCorteLateral(page));
  await aud.captura("Passo 7 · tela inicial no celular");

  const mapa = page.locator("#mapa");
  await eu.rolarAte(mapa);
  const caixa = (await mapa.boundingBox())!;
  await page.touchscreen.tap(caixa.x + caixa.width / 2, caixa.y + caixa.height / 2);
  await aud.verificar("Passo 7 ✔ O mapa funciona com o dedo", "tocar no mapa escolhe um local",
    () => expect(page.locator("#local-atual")).toContainText(/-[A-Z]{2}/), () => page.locator("#local-atual").innerText());
  await aud.captura("Passo 7 · toque no mapa escolheu um local", { paginaInteira: false });

  await eu.digitar(page.locator("#busca"), "Rio Verde");
  await eu.clicar(page.locator("#sugestoes li[data-codigo]", { hasText: /^Rio Verde-GO$/ }));
  await expect(page.locator("#local-atual")).toContainText("Rio Verde-GO");
  await eu.clicar(page.getByRole("link", { name: "Seguir para a comparação →" }));

  await eu.clicar(page.locator("#usar-lavoura"));
  await eu.data(page.locator("#colheita"), "2027-01-20");
  await eu.clicar(page.locator('input[name="solo"][value="argilosa"]'));
  await eu.clicar(page.locator('input[name="grupo"][value="nao_sei"]'));
  await aud.verificar("Passo 7 ✔ Entradas: nada cortado na lateral", "sem rolagem lateral", () => semCorteLateral(page));
  await aud.verificar("Passo 7 ✔ O menu de etapas quebra linha", "menu inteiro dentro da tela, em mais de uma linha",
    async () => {
      const nav = page.getByRole("navigation").first();
      const b = (await nav.boundingBox())!;
      expect(b.x + b.width).toBeLessThanOrEqual(391);
      const tops = new Set(await nav.locator("li").evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().top))));
      expect(tops.size).toBeGreaterThan(1);
      return `${tops.size} linhas`;
    });
  await aud.captura("Passo 7 · entradas no celular");
  await eu.clicar(page.getByRole("button", { name: "Seguir para a metodologia" }));
  await eu.clicar(page.locator('input[name="metodologia"][value="comparar_alternativas"]'));
  await aud.captura("Passo 7 · metodologia no celular");
  await eu.clicar(page.getByRole("button", { name: "Calcular" }));

  const real = page.locator("#resultado-real");
  await expect(real.locator("h2").first()).toHaveText(/Resultado calculado|Resultado parcial/, { timeout: 300_000 });
  await eu.ler(1500);
  await aud.verificar("Passo 7 ✔ Resultado: nada cortado na lateral", "sem rolagem lateral", () => semCorteLateral(page));
  const primeiro = real.locator("details.group").first();
  await eu.clicar(primeiro.locator("summary"));
  await aud.verificar("Passo 7 ✔ Alternativa abre com o dedo", "riscos e margem visíveis",
    async () => { await expect(primeiro).toContainText("Risco oficial (ZARC)"); await expect(primeiro.locator("table")).toContainText("Central"); });
  await aud.captura("Passo 7 · resultado no celular");
});
