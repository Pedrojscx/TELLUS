import { expect, test } from "./auditoria";

test("Tela de cálculo simula sucesso, fonte com cópia guardada e falha sem cópia", async ({ page, aud }) => {
  await page.goto("/comparacao/carga");
  await aud.verificar("Tela de simulação marcada como exemplo", "faixa \"DADO DE EXEMPLO\"",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").first()).toBeVisible());
  for (const [botao, esperado] of [
    ["Simular: tudo certo", /Resultado completo|Ver resultado/],
    ["Simular: fonte com cache", /cópia guardada|cache/],
    ["Simular: falha sem cache", /sem cópia guardada|Não foi possível/],
  ] as const) {
    await page.getByRole("button", { name: botao }).click();
    const area = page.locator("main");
    await aud.verificar(`${botao}: estado legível`, String(esperado), () => expect(area).toContainText(esperado));
    await aud.captura(botao.replace("Simular: ", "simulacao "));
  }
  await aud.verificar("Falha sem cache não mostra resultado como final", "nenhum \"Resultado completo.\" após a falha",
    () => expect(page.locator("main").getByText("Resultado completo.", { exact: true })).toHaveCount(0));
});

test("Tela de erros mostra os três estados de uma fonte", async ({ page, aud }) => {
  await page.goto("/comparacao/erros");
  for (const t of ["Fonte respondeu", "Fonte fora do ar, com cópia guardada", "Fonte fora do ar, sem cópia guardada"]) {
    await aud.verificar(`Estado "${t}"`, t, () => expect(page.getByText(t).first()).toBeVisible());
  }
  await aud.verificar("Erro diz o que fazer", "\"O que fazer\"", () => expect(page.getByText("O que fazer").first()).toBeVisible());
  await aud.captura("tres estados de uma fonte");
});
