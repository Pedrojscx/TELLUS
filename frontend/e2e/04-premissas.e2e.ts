import { expect, test } from "./auditoria";
import { escolherRioVerde, esperarResultado, preencherEntradas } from "./fluxo";

test("Premissas mostram os padrões reais e a edição chega ao cálculo", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await page.locator('input[name="metodologia"][value="comparar_alternativas"]').check();
  await page.getByRole("button", { name: "Calcular" }).click(); // grava a metodologia na sessão
  await page.goto("/comparacao/premissas");

  await aud.verificar("Padrões reais carregados para a lavoura", "\"Padrões reais para Rio Verde-GO\"",
    () => expect(page.locator("#padroes-reais")).toContainText("Padrões reais para Rio Verde-GO"),
    () => page.locator("#padroes-reais").innerText());
  const milho = page.locator('[data-premissa="preco_milho"]');
  await aud.verificar("Preço do milho com fonte CEPEA", "padrão numérico em R$/saca, fonte Cepea/Esalq",
    async () => { await expect(milho.locator("[data-fonte]")).toContainText(/cepea/i); await expect(milho.locator("[data-padrao]")).toHaveText(/\d/); },
    async () => `${await milho.locator("[data-padrao]").innerText()} · ${await milho.locator("[data-fonte]").innerText()}`);
  const custo = page.locator('[data-premissa="custo_milho"]');
  await aud.verificar("Custo do milho com fonte Conab", "fonte Conab", () => expect(custo.locator("[data-fonte]")).toContainText("Conab"),
    async () => `${await custo.locator("[data-padrao]").innerText()} · ${await custo.locator("[data-fonte]").innerText()}`);
  await aud.verificar("Sem faixa de dado de exemplo com padrões reais", "faixa oculta",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").filter({ visible: true })).toHaveCount(0));
  await aud.captura("padroes reais de Rio Verde-GO");

  await milho.locator("input").fill("70");
  await aud.verificar("Edição mostra o padrão ao lado do novo valor", "\"Editado por você (padrão …)\"",
    () => expect(milho.locator("[data-saida]")).toContainText("Editado por você"), () => milho.locator("[data-saida]").innerText());

  const sorgo = page.locator('[data-cotacao="preco_sorgo"]');
  await sorgo.locator('input[name="valor"]').fill("55");
  await sorgo.locator('input[name="origem"]').fill("Cooperativa de Rio Verde (teste)");
  await sorgo.locator('input[name="data"]').fill("2030-01-01");
  await aud.verificar("Cotação com data futura é recusada", "erro sobre data no futuro",
    () => expect(sorgo.locator("[data-erros]")).toContainText(/futuro/), () => sorgo.locator("[data-erros]").innerText());
  await sorgo.scrollIntoViewIfNeeded();
  await aud.captura("cotacao do sorgo com data futura recusada", { paginaInteira: false });

  await sorgo.locator('input[name="data"]').fill("2026-11-10");
  await aud.verificar("Cotação completa aceita", "sem erros na cotação",
    () => expect(sorgo.locator("[data-erros] li")).toHaveCount(0), () => sorgo.locator("[data-saida]").innerText());
  await aud.captura("premissas editadas");

  await page.getByRole("link", { name: "4. Resultado" }).click();
  await esperarResultado(page, aud);
  const real = page.locator("#resultado-real");
  const cartaoMilho = real.locator("details.group", { hasText: "Milho" }).first();
  await cartaoMilho.locator("summary").click();
  await aud.verificar("Preço editado chega ao cálculo do milho", "hipótese \"preco_r_saca (Milho 2ª safra): … → 70 … (editado pelo produtor)\"",
    () => expect(cartaoMilho).toContainText(/preco_r_saca \(Milho 2ª safra\): .+ → 70 .+editado pelo produtor/),
    async () => (await cartaoMilho.innerText()).split("\n").find((l) => l.includes("→")) ?? "sem linha com →");
  await cartaoMilho.scrollIntoViewIfNeeded();
  await aud.captura("milho com o preco editado", { paginaInteira: false });

  const cartaoSorgo = real.locator("details.group", { hasText: "Sorgo" }).first();
  await aud.verificar("Sorgo entra com a cotação informada", "alternativa de sorgo com margem",
    () => expect(cartaoSorgo).toBeVisible(), async () => (await cartaoSorgo.count()) ? await cartaoSorgo.locator("summary").innerText() : "nenhuma alternativa de sorgo");
  await cartaoSorgo.locator("summary").click();
  await aud.verificar("Cotação do sorgo aparece como informada pelo produtor", "origem informada no resultado",
    () => expect(cartaoSorgo).toContainText("Cooperativa de Rio Verde (teste)"));
  await cartaoSorgo.scrollIntoViewIfNeeded();
  await aud.captura("sorgo com a cotacao informada", { paginaInteira: false });
});

// DEFEITO CONHECIDO (encontrado por esta bateria em 15/11/2026): com grupo "não sei", o valor padrão da premissa
// editada não volta na resposta (valor_padrao vem nulo porque a seção economia por cultura fica indisponível).
// O resultado mostra "sem padrão com fonte → 70" em vez de "padrão 67,34 → 70". A edição chega ao cálculo
// (a margem muda); só o padrão some. test.fail: quando corrigirem, tirar esta marca.
test("Defeito conhecido: com grupo \"não sei\", o resultado mostra o padrão ao lado do preço editado", async ({ page, aud }) => {
  test.fail(true, "Com grupo \"não sei\", valor_padrao vem nulo e a tela diz \"sem padrão com fonte\".");
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await page.locator('input[name="metodologia"][value="comparar_alternativas"]').check();
  await page.getByRole("button", { name: "Calcular" }).click();
  await page.goto("/comparacao/premissas");
  await expect(page.locator("#padroes-reais")).toContainText("Padrões reais");
  await page.locator('[data-premissa="preco_milho"] input').fill("70");
  await page.getByRole("link", { name: "4. Resultado" }).click();
  await esperarResultado(page, aud);
  const cartao = page.locator("#resultado-real details.group", { hasText: "Milho" }).first();
  await cartao.locator("summary").click();
  await aud.verificar("Padrão aparece ao lado do novo valor", "\"padrão 67,34 → 70\" (ou o padrão vigente)",
    () => expect(cartao).toContainText(/padrão [\d,.]+ → 70/, { timeout: 3_000 }),
    async () => (await cartao.innerText()).split("\n").find((l) => l.includes("→")) ?? "sem linha com →");
});
