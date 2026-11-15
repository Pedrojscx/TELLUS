import { expect, test } from "./auditoria";
import { escolherRioVerde, preencherEntradas } from "./fluxo";

test("Entradas vazias não seguem e explicam o que falta", async ({ page, aud }) => {
  await page.goto("/comparacao/entradas");
  await page.locator("#limpar").click();
  await page.getByRole("button", { name: "Seguir para a metodologia" }).click();
  await aud.verificar("Resumo de erros aparece", "lista do que falta, em português",
    () => expect(page.locator("#resumo-erros")).toBeVisible(), () => page.locator("#resumo-erros").innerText());
  await aud.verificar("Continua nas Entradas", "URL /comparacao/entradas", () => expect(page).toHaveURL(/\/comparacao\/entradas/));
  await aud.captura("erros de entradas vazias");
});

test("Água disponível em mm aceita só número positivo", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await page.goto("/comparacao/entradas");
  await page.locator("#usar-lavoura").click();
  await page.locator("#colheita").fill("2027-01-20");
  await page.locator('input[name="solo"][value="mm"]').check();
  await page.locator("#cad-mm").fill("-5");
  await page.locator('input[name="grupo"][value="I"]').check();
  await page.getByRole("button", { name: "Seguir para a metodologia" }).click();
  await aud.verificar("Valor negativo recusado", "erro sobre a água disponível",
    () => expect(page.locator("#resumo-erros")).toBeVisible(), () => page.locator("#resumo-erros").innerText());
  await aud.captura("agua disponivel negativa recusada");
});

test("Caso de referência preenchido segue para a metodologia", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud);
  await aud.verificar("Sem faixa de dado de exemplo com lavoura real", "nenhum \"DADO DE EXEMPLO\"",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real")).toHaveCount(0));
  await aud.captura("metodologia aberta");
});

test("Metodologia sem escolha não calcula", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await page.getByRole("button", { name: "Calcular" }).click();
  await aud.verificar("Pede para escolher a forma de calcular", "mensagem de erro da metodologia",
    () => expect(page.locator("#erro-metodologia")).toBeVisible(), () => page.locator("#erro-metodologia").innerText());
  await aud.verificar("Continua na metodologia", "URL /comparacao/metodologia", () => expect(page).toHaveURL(/metodologia/));
  await aud.captura("metodologia sem escolha");
});
