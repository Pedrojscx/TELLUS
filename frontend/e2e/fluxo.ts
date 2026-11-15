// Passos do produtor reaproveitados pelas suítes. Sempre pela interface (nada injetado no navegador),
// com captura e verificação em cada passo.
import type { Page } from "@playwright/test";
import { expect, type Auditoria } from "./auditoria";

export const COLHEITA = "2027-01-20";
const TEMPO_CALCULO = 240_000;

/** Tela inicial → busca "Rio Verde" → escolhe Rio Verde-GO na lista. */
export async function escolherRioVerde(page: Page, aud: Auditoria, comCaptura = true): Promise<void> {
  await page.goto("/");
  await page.locator("#busca").fill("Rio Verde");
  const opcao = page.locator('#sugestoes li[data-codigo]', { hasText: /^Rio Verde-GO$/ });
  await aud.verificar("Busca de município sugere Rio Verde-GO", "opção \"Rio Verde-GO\" na lista",
    () => expect(opcao).toBeVisible(), () => page.locator("#sugestoes").innerText());
  if (comCaptura) await aud.captura("busca por Rio Verde", { paginaInteira: false });
  await opcao.click();
  await aud.verificar("Local escolhido aparece no topo do seletor", "Rio Verde-GO",
    () => expect(page.locator("#local-atual")).toContainText("Rio Verde-GO"), () => page.locator("#local-atual").innerText());
  await aud.verificar("Lavoura guardada para a comparação", "lavoura salva no navegador (sessionStorage)",
    () => expect.poll(() => page.evaluate(() => sessionStorage.getItem("tellus.lavoura.v1"))).toContain("Rio Verde"),
    async () => (await page.evaluate(() => sessionStorage.getItem("tellus.lavoura.v1")))?.slice(0, 120) ?? "nada");
  if (comCaptura) await aud.captura("Rio Verde-GO escolhido");
}

/** Entradas do caso de referência: lavoura confirmada, colheita 20/01/2027, argilosa, grupo "não sei". */
export async function preencherEntradas(page: Page, aud: Auditoria, comCaptura = true): Promise<void> {
  await page.goto("/comparacao/entradas");
  await page.locator("#usar-lavoura").click();
  await aud.verificar("Área confirmada a partir da lavoura da tela inicial", "estado da área com Rio Verde",
    () => expect(page.locator("#area-estado")).toContainText("Rio Verde"), () => page.locator("#area-estado").innerText());
  await page.locator("#colheita").fill(COLHEITA);
  await page.locator('input[name="solo"][value="argilosa"]').check();
  await page.locator('input[name="grupo"][value="nao_sei"]').check();
  if (comCaptura) await aud.captura("entradas preenchidas");
  await page.getByRole("button", { name: /Seguir para a metodologia|Continue to method/ }).click();
  await aud.verificar("Entradas válidas levam à metodologia", "URL /comparacao/metodologia",
    () => expect(page).toHaveURL(/\/comparacao\/metodologia/), async () => page.url());
}

/** Metodologia "comparar alternativas" → Calcular → espera o resultado real. */
export async function calcular(page: Page, aud: Auditoria): Promise<void> {
  await page.locator('input[name="metodologia"][value="comparar_alternativas"]').check();
  await aud.captura("metodologia: comparar as alternativas");
  await page.getByRole("button", { name: /^(Calcular|Calculate)$/ }).click();
  await expect(page).toHaveURL(/\/comparacao\/resultado/);
  await esperarResultado(page, aud);
}

export async function esperarResultado(page: Page, aud: Auditoria): Promise<void> {
  const titulo = page.locator("#resultado-real h2").first();
  await aud.verificar("Cálculo real termina e mostra o estado do resultado", "\"Resultado calculado\" ou \"Resultado parcial\"",
    () => expect(titulo).toHaveText(/Resultado calculado|Resultado parcial|Result calculated|Partial result/, { timeout: TEMPO_CALCULO }),
    () => titulo.innerText());
}
