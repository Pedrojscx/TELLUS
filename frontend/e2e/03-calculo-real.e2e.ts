import { expect, test } from "./auditoria";
import { calcular, escolherRioVerde, preencherEntradas } from "./fluxo";

test("Caso de referência: Rio Verde-GO, colheita 20/01/2027, argilosa, grupo \"não sei\"", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await calcular(page, aud);
  const real = page.locator("#resultado-real");
  await aud.verificar("Contrato da API informado", "Contrato 1.2.0", () => expect(real).toContainText("Contrato 1.2.0"));
  await aud.verificar("Sem faixa de dado de exemplo no resultado real", "nenhum \"DADO DE EXEMPLO\" visível",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").filter({ visible: true })).toHaveCount(0));
  const cartoes = real.locator("details.group");
  await aud.verificar("Lista ordenada de alternativas dentro do ZARC", "ao menos 1 alternativa",
    async () => { expect(await cartoes.count()).toBeGreaterThan(0); }, async () => `${await cartoes.count()} alternativas`);
  await aud.verificar("Critério de ordem escrito", "começa por \"maior margem no cenário conservador\"",
    () => expect(real.getByText("Critério de ordem:").locator("..")).toContainText("maior margem no cenário conservador"),
    () => real.getByText("Critério de ordem:").locator("..").innerText());
  await aud.captura("resultado calculado");

  const primeiro = cartoes.first();
  await primeiro.locator("summary").click();
  for (const [desc, texto] of [["Risco oficial do ZARC separado", "Risco oficial (ZARC)"],
                               ["Risco histórico separado", "Risco histórico de falta de água"],
                               ["Fontes da alternativa", "Fontes"]] as const) {
    await aud.verificar(desc, texto, () => expect(primeiro).toContainText(texto));
  }
  await aud.verificar("Margem em 3 cenários", "Conservador, Central e Favorável",
    async () => { for (const c of ["Conservador", "Central", "Favorável"]) await expect(primeiro.locator("table")).toContainText(c); },
    () => primeiro.locator("table").innerText());
  await aud.verificar("Fontes citam a série NASA (IMERG/POWER), o ZARC e a Conab", "IMERG/POWER, ZARC e Conab entre as fontes",
    async () => { for (const f of ["IMERG/POWER", "ZARC", "Conab"]) await expect(primeiro).toContainText(f); });
  await primeiro.scrollIntoViewIfNeeded();
  await aud.captura("primeira alternativa aberta", { paginaInteira: false });

  await real.getByText("O que foi consultado e calculado").click();
  await aud.verificar("Recomendação listada como pronta", "\"Recomendação (ordem das alternativas): pronto\"",
    () => expect(real.locator("details").first()).toContainText("Recomendação (ordem das alternativas): pronto"),
    () => real.locator("details").first().innerText());
  await real.getByText("O que foi consultado e calculado").scrollIntoViewIfNeeded();
  await aud.captura("o que foi consultado e calculado", { paginaInteira: false });

  const ctx = real.getByRole("heading", { name: "Contexto da região (opcional)" }).locator("..");
  await aud.verificar("Contextos opcionais avisam que não entram no cálculo", "\"não entra no cálculo\"",
    () => expect(ctx).toContainText("não entra no cálculo"));
  await aud.verificar("Vegetação e umidade do solo presentes", "MODIS e SMAP",
    async () => { await expect(ctx).toContainText("MODIS"); await expect(ctx).toContainText("SMAP"); });
  await ctx.scrollIntoViewIfNeeded();
  await aud.captura("contexto da regiao", { paginaInteira: false });

  await aud.verificar("Nenhum texto trata risco como previsão", "sem \"vai chover\" nem \"previsão de\"",
    async () => {
      const t = (await real.innerText()).toLowerCase();
      expect(t).not.toContain("vai chover");
      expect(t).not.toMatch(/previsão de (chuva|safra|colheita|produtividade)/);
    });
});

// Regressão do achado de 15/11/2026 (grupo "não sei"), corrigido em seguida; antes era um test.fail.
test("Grupo \"não sei\": \"O que foi consultado\" lista as fontes de clima e as culturas calculadas por grupo", async ({ page, aud }) => {
  await escolherRioVerde(page, aud, false);
  await preencherEntradas(page, aud, false);
  await calcular(page, aud);
  const lista = page.locator("#resultado-real details").first();
  await lista.locator("summary").click();
  await aud.verificar("Fontes de dados listadas", "NASA GPM IMERG e NASA POWER entre as etapas",
    () => expect(lista).toContainText("NASA GPM IMERG", { timeout: 3_000 }), () => lista.innerText());
  await aud.verificar("Culturas não aparecem como falha", "nenhum \"✕\" nas culturas",
    () => expect(lista).not.toContainText("✕", { timeout: 3_000 }), () => lista.innerText());
  await aud.verificar("Culturas indicadas como calculadas por grupo", "\"por grupo, na recomendação\"",
    () => expect(lista).toContainText("por grupo, na recomendação"));
  await lista.scrollIntoViewIfNeeded();
  await aud.captura("o que foi consultado com grupo nao sei", { paginaInteira: false });
});
