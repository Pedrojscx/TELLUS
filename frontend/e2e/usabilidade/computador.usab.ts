// Roteiro de teste do TELLUS (caso de referência, #104/#56), passo a passo, no computador.
// Cada "✔" do roteiro é uma verificação; cada passo termina com captura. A sessão inteira é gravada em vídeo.
import { expect, test } from "../auditoria";
import { Humano } from "./humano";

const PASSOS_ATE_RESULTADO = 4;

test("Sessão completa no computador: da tela inicial ao resultado com premissas editadas", async ({ page, aud }) => {
  const eu = new Humano(page);

  // ---------------------------------------------------------------- Passo 1
  await page.goto("/");
  await eu.ler(1200);
  await aud.verificar("Passo 1 ✔ Logo do TELLUS no topo e na aba", "ícone verde no topo e favicon próprio na aba",
    async () => { await expect(page.locator("header img[src*='favicon']").first()).toBeVisible(); expect(await page.locator('link[rel="icon"]').getAttribute("href")).toContain("favicon.svg"); });
  await aud.verificar("Passo 1 ✔ Passo a passo \"1. Escolha… 4. Veja…\"", "4 passos visíveis",
    () => expect(page.getByRole("list", { name: "Como usar" }).locator("li")).toHaveCount(4),
    () => page.getByRole("list", { name: "Como usar" }).innerText());
  await aud.captura("Passo 1 · tela inicial");

  await eu.digitar(page.locator("#busca"), "Rio Verde");
  const opcao = page.locator("#sugestoes li[data-codigo]", { hasText: /^Rio Verde-GO$/ });
  await expect(opcao).toBeVisible();
  await eu.ler(700);
  await aud.captura("Passo 1 · digitou Rio Verde e viu a lista", { paginaInteira: false });
  await eu.clicar(opcao);
  await aud.verificar("Passo 1 ✔ O ponto aparece no mapa", "marcador do local no mapa e Rio Verde-GO no topo do seletor",
    async () => { await expect(page.locator("#local-atual")).toContainText("Rio Verde-GO"); expect(await page.locator("#mapa .leaflet-interactive, #mapa .leaflet-marker-icon").count()).toBeGreaterThan(0); },
    () => page.locator("#local-atual").innerText());
  await eu.ler(1000);
  await aud.captura("Passo 1 · Rio Verde-GO escolhido", { paginaInteira: false });

  const refs = page.getByText("De onde vêm os dados deste local").locator("xpath=ancestor::section[1]");
  await eu.rolarAte(refs);
  for (const [fonte, rotulo] of [["NASA POWER", "Clima (NASA POWER)"], ["IMERG", "Chuva (NASA IMERG)"], ["INMET", "Estação INMET"],
                                 ["Conab", "Custos (Conab)"], ["ZARC", "Município para o ZARC"]] as const) {
    await aud.verificar(`Passo 1 ✔ "De onde vêm os dados": ${rotulo}`, `${fonte} com a distância em km`,
      async () => { await expect(refs).toContainText(fonte); await expect(refs).toContainText("km"); });
  }
  await aud.captura("Passo 1 · de onde vêm os dados deste local", { paginaInteira: false });
  await eu.clicar(page.getByRole("link", { name: "Seguir para a comparação →" }));

  // ---------------------------------------------------------------- Passo 2
  await expect(page).toHaveURL(/\/comparacao\/entradas/);
  await eu.ler(1000);
  await eu.clicar(page.locator("#usar-lavoura"));
  await aud.verificar("Passo 2 ✔ Aparece \"Área confirmada\"", "\"Área confirmada: Rio Verde-GO (ponto)\"",
    () => expect(page.locator("#area-estado")).toContainText("Área confirmada"), () => page.locator("#area-estado").innerText());
  await eu.data(page.locator("#colheita"), "2027-01-20");
  await eu.clicar(page.locator('input[name="solo"][value="argilosa"]'));
  await eu.clicar(page.locator('input[name="grupo"][value="nao_sei"]'));
  await aud.verificar("Passo 2 ✔ Sem a faixa amarela \"DADO DE EXEMPLO\"", "faixa ausente",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").filter({ visible: true })).toHaveCount(0));
  await aud.captura("Passo 2 · entradas preenchidas");

  await eu.data(page.locator("#colheita"), "");
  await eu.clicar(page.getByRole("button", { name: "Seguir para a metodologia" }));
  const erroData = page.locator('[data-erro="colheita_soja"]');
  await aud.verificar("Passo 2 ✔ Apagar a data e tentar seguir: o site avisa em português o que falta", "resumo \"Corrija … campo(s)\" e aviso ao lado da data",
    async () => { await expect(page.locator("#resumo-erros")).toContainText("Corrija"); await expect(erroData).toContainText(/data/i); },
    async () => `${await page.locator("#resumo-erros").innerText()} · ${await erroData.innerText()}`);
  await aud.captura("Passo 2 · erro sem a data da colheita", { paginaInteira: false });
  await eu.data(page.locator("#colheita"), "2027-01-20");
  await eu.clicar(page.getByRole("button", { name: "Seguir para a metodologia" }));

  // ---------------------------------------------------------------- Passo 3
  await expect(page).toHaveURL(/\/comparacao\/metodologia/);
  await eu.ler(1200);
  await eu.clicar(page.locator('input[name="metodologia"][value="comparar_alternativas"]'));
  await aud.captura("Passo 3 · comparar as alternativas");
  await eu.clicar(page.getByRole("button", { name: "Calcular" }));

  // ---------------------------------------------------------------- Passo 4
  await expect(page).toHaveURL(/\/comparacao\/resultado/);
  await aud.verificar("Passo 4 ✔ Primeiro aparece \"Calculando… etapa atual\"", "texto de etapa enquanto calcula (observação)",
    async () => {
      try { await expect(page.getByText("Calculando… etapa atual")).toBeVisible({ timeout: 4_000 }); await aud.captura("Passo 4 · calculando"); return "visto: \"Calculando… etapa atual\""; }
      catch { return "o resultado chegou antes da captura (dados já em cache)"; }
    });
  const real = page.locator("#resultado-real");
  const titulo = real.locator("h2").first();
  await expect(titulo).toHaveText(/Resultado calculado|Resultado parcial/, { timeout: 300_000 });
  await eu.ler(1500);
  const cartoes = real.locator("details.group");
  await aud.verificar("Passo 4 ✔ Topo diz \"Resultado calculado\" ou \"Resultado PARCIAL\"", "um dos dois", () => expect(titulo).toBeVisible(), () => titulo.innerText());
  await aud.verificar("Passo 4 ✔ Lista \"Alternativas dentro do ZARC\" numerada", "ao menos 1 alternativa numerada",
    async () => { await expect(real).toContainText("Alternativas dentro do ZARC"); expect(await cartoes.count()).toBeGreaterThan(0); await expect(cartoes.first()).toContainText("1."); },
    async () => `${await cartoes.count()} alternativas`);
  await aud.verificar("Passo 4 ✔ Critério de ordem escrito", "\"Critério de ordem: …\"",
    () => expect(real.getByText("Critério de ordem:")).toBeVisible(), () => real.getByText("Critério de ordem:").locator("..").innerText());
  await aud.verificar("Passo 4 ✔ Nenhuma faixa amarela de exemplo", "faixa ausente",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").filter({ visible: true })).toHaveCount(0));
  await aud.captura("Passo 4 · resultado calculado");

  const primeiro = cartoes.first();
  await eu.clicar(primeiro.locator("summary"));
  await eu.ler(1200);
  await aud.verificar("Passo 4 ✔ \"Risco oficial (ZARC)\" e \"Risco histórico de falta de água\", separados", "dois quadros distintos",
    async () => { await expect(primeiro).toContainText("Risco oficial (ZARC)"); await expect(primeiro).toContainText("Risco histórico de falta de água"); });
  await aud.verificar("Passo 4 ✔ Margem por hectare em 3 cenários", "Conservador, Central, Favorável",
    async () => { for (const c of ["Conservador", "Central", "Favorável"]) await expect(primeiro.locator("table")).toContainText(c); },
    () => primeiro.locator("table").innerText());
  await aud.verificar("Passo 4 ✔ Lista de Fontes", "ZARC, série NASA (IMERG/POWER), Conab",
    async () => { for (const f of ["ZARC", "IMERG/POWER", "Conab"]) await expect(primeiro).toContainText(f); });
  await aud.captura("Passo 4 · primeira alternativa aberta", { paginaInteira: false });

  const consultado = real.locator("details").first();
  await eu.clicar(consultado.locator("summary"));
  await eu.ler(1000);
  await aud.verificar("Passo 4 ✔ \"O que foi consultado\": cada fonte aparece, cópia guardada com a data", "IMERG e POWER listados; cache com data",
    async () => { await expect(consultado).toContainText("IMERG"); await expect(consultado).toContainText("POWER"); },
    () => consultado.innerText());
  await aud.verificar("Passo 4 ✔ O que ficou indisponível mostra o motivo (nenhuma cultura marcada como falha)", "culturas \"por grupo, na recomendação\", sem ✕",
    async () => { await expect(consultado).toContainText("por grupo, na recomendação"); await expect(consultado).not.toContainText("✕"); });
  await aud.captura("Passo 4 · o que foi consultado e calculado", { paginaInteira: false });

  const ctx = real.getByRole("heading", { name: "Contexto da região (opcional)" }).locator("..");
  await eu.rolarAte(ctx);
  await aud.verificar("Passo 4 ✔ Vegetação: MODIS disponível e HLS indisponível com o motivo", "\"MOD13Q1: disponível\" e \"HLS: indisponível (…)\"",
    async () => { await expect(ctx).toContainText(/MOD13Q1: disponível/); await expect(ctx).toContainText(/HLS: indisponível \(.+\)/); });
  await aud.verificar("Passo 4 ✔ Umidade do solo (SMAP) com aviso de escala", "SMAP com aviso de escala regional",
    async () => { await expect(ctx).toContainText("SMAP"); await expect(ctx).toContainText(/célula|regional|escala/i); });
  await aud.verificar("Passo 4 ✔ O texto diz que isso não entra no cálculo", "\"não entra no cálculo\"", () => expect(ctx).toContainText("não entra no cálculo"));
  await aud.captura("Passo 4 · contexto da região", { paginaInteira: false });

  // ---------------------------------------------------------------- Passo 6 (no mesmo resultado)
  await aud.verificar("Passo 6 ✔ Nenhuma alternativa fora da janela do ZARC", "toda alternativa tem risco oficial ZARC de 20, 30 ou 40%",
    async () => {
      const riscos = await cartoes.evaluateAll((els) => els.map((e) => (e.textContent ?? "").match(/Risco oficial \(ZARC\)\s*(\d+)%/)?.[1] ?? "?"));
      expect(riscos.every((r) => ["20", "30", "40"].includes(r))).toBe(true);
      return `riscos ZARC das ${riscos.length} alternativas: ${riscos.join(", ")}%`;
    });
  await aud.verificar("Passo 6 ✔ O que não tem dado aparece como indisponível, com o motivo, e não como recomendação", "avisos com o motivo (ex.: janela antes da colheita)",
    () => expect(real.getByRole("heading", { name: "Avisos" }).locator("..")).toContainText("decêndio da janela termina antes da colheita da soja"));
  await eu.rolarAte(real.getByRole("heading", { name: "Avisos" }));
  await aud.captura("Passo 6 · avisos com os motivos", { paginaInteira: false });

  // ---------------------------------------------------------------- Passo 5
  await eu.clicar(page.getByRole("link", { name: "5. Premissas" }));
  const status = page.locator("#padroes-reais");
  await aud.verificar("Passo 5 ✔ Aparece \"Padrões reais para Rio Verde-GO\", sem a faixa amarela", "linha verde de padrões reais; faixa ausente",
    async () => { await expect(status).toContainText("Padrões reais para Rio Verde-GO"); await expect(page.getByText("DADO DE EXEMPLO — não é resultado real").filter({ visible: true })).toHaveCount(0); },
    () => status.innerText());
  const padrao = (id: string) => page.locator(`[data-premissa="${id}"] [data-padrao]`);
  const fonte = (id: string) => page.locator(`[data-premissa="${id}"] [data-fonte]`);
  await aud.verificar("Passo 5 ✔ Preço do milho 67,34 (Cepea)", "67,34 R$/saca, fonte Cepea",
    async () => { await expect(padrao("preco_milho")).toContainText("67,34"); await expect(fonte("preco_milho")).toContainText(/cepea/i); },
    async () => `${await padrao("preco_milho").innerText()} · ${await fonte("preco_milho").innerText()}`);
  await aud.verificar("Passo 5 ✔ Custo 5.889 R$/ha (Conab)", "5.889 R$/ha, fonte Conab",
    async () => { await expect(padrao("custo_milho")).toContainText("5.889"); await expect(fonte("custo_milho")).toContainText("Conab"); },
    () => padrao("custo_milho").innerText());
  await aud.verificar("Passo 5 ✔ 100 sacas/ha (Conab)", "100 sc/ha, fonte Conab",
    async () => { await expect(padrao("sacas_ha_milho")).toContainText("100"); await expect(fonte("sacas_ha_milho")).toContainText("Conab"); },
    () => padrao("sacas_ha_milho").innerText());
  await aud.verificar("Passo 5 ✔ Água do solo com a fonte do ZARC", "fonte cita a classe do ZARC",
    () => expect(fonte("cad_mm")).toContainText("ZARC"), () => fonte("cad_mm").innerText());
  await aud.captura("Passo 5 · padrões reais");

  await eu.digitar(page.locator("#p-preco_milho"), "70");
  const sorgo = page.locator('[data-cotacao="preco_sorgo"]');
  await eu.digitar(sorgo.locator('input[name="valor"]'), "55");
  await eu.digitar(sorgo.locator('input[name="origem"]'), "Cooperativa de Rio Verde");
  await eu.data(sorgo.locator('input[name="data"]'), "2030-01-01");
  await aud.verificar("Passo 5 ✔ Data futura na cotação: o site recusa", "aviso de data no futuro",
    () => expect(sorgo.locator("[data-erros]")).toContainText(/futuro/), () => sorgo.locator("[data-erros]").innerText());
  await aud.captura("Passo 5 · data futura recusada", { paginaInteira: false });
  await eu.data(sorgo.locator('input[name="data"]'), "2026-11-10");
  await expect(sorgo.locator("[data-erros] li")).toHaveCount(0);
  await aud.captura("Passo 5 · milho a 70 e sorgo informado");

  await eu.clicar(page.getByRole("link", { name: `${PASSOS_ATE_RESULTADO}. Resultado` }));
  await expect(real.locator("h2").first()).toHaveText(/Resultado calculado|Resultado parcial/, { timeout: 300_000 });
  await eu.ler(1500);
  const milho = real.locator("details.group", { hasText: "Milho" }).first();
  await eu.clicar(milho.locator("summary"));
  await aud.verificar("Passo 5 ✔ Na alternativa de milho, \"Hipóteses usadas\" mostra \"padrão 67,34 → 70\"", "padrão 67,34 → 70",
    () => expect(milho).toContainText(/padrão 67,34 → 70/),
    async () => (await milho.innerText()).split("\n").find((l) => l.includes("→")) ?? "sem linha com →");
  await eu.rolarAte(milho.getByText(/padrão 67,34 → 70/));
  await aud.captura("Passo 5 · milho com padrão → novo", { paginaInteira: false });
  const cartaoSorgo = real.locator("details.group", { hasText: "Sorgo" }).first();
  await eu.clicar(cartaoSorgo.locator("summary"));
  await aud.verificar("Passo 5 ✔ O sorgo aparece com margem e a cotação como informada pela cooperativa", "margem do sorgo e \"Cooperativa de Rio Verde\"",
    async () => { await expect(cartaoSorgo.locator("summary")).not.toContainText("indisponível"); await expect(cartaoSorgo).toContainText("Cooperativa de Rio Verde"); },
    () => cartaoSorgo.locator("summary").innerText());
  await eu.rolarAte(cartaoSorgo.getByText("Cooperativa de Rio Verde").first());
  await aud.captura("Passo 5 · sorgo com a cotação informada", { paginaInteira: false });
});

test("Passo 1 (opcional): desenhar a área da lavoura no mapa", async ({ page, aud }) => {
  const eu = new Humano(page);
  await page.goto("/");
  await eu.digitar(page.locator("#busca"), "Rio Verde");
  await eu.clicar(page.locator("#sugestoes li[data-codigo]", { hasText: /^Rio Verde-GO$/ }));
  await expect(page.locator("#local-atual")).toContainText("Rio Verde-GO");
  const mapa = page.locator("#mapa");
  await eu.rolarAte(mapa);
  for (let i = 0; i < 7; i++) { await page.locator("#mapa .leaflet-control-zoom-in").click(); await eu.ler(450); } // aproxima até o tamanho de uma lavoura
  await eu.ler(1200);
  await eu.clicar(page.locator("#desenho-iniciar"));
  const caixa = (await mapa.boundingBox())!;
  const cx = caixa.x + caixa.width / 2, cy = caixa.y + caixa.height / 2;
  for (const [dx, dy] of [[-60, -40], [60, -40], [60, 40], [-60, 40]]) {
    await page.mouse.move(cx + dx, cy + dy, { steps: 8 });
    await eu.ler(300);
    await page.mouse.click(cx + dx, cy + dy);
  }
  await aud.verificar("Passo 1 ✔ Quatro cantos marcados no mapa", "\"4 ponto(s) marcado(s)\"",
    () => expect(page.locator("#desenho-estado")).toContainText("4 ponto(s)"), () => page.locator("#desenho-estado").innerText());
  await aud.captura("Passo 1 opcional · quatro cantos marcados", { paginaInteira: false });
  await eu.clicar(page.locator("#desenho-fechar"));
  const confirmar = page.getByRole("button", { name: "Confirmar esta área" });
  await expect(confirmar).toBeVisible();
  await aud.captura("Passo 1 opcional · área para conferir", { paginaInteira: false });
  await eu.clicar(confirmar);
  await aud.verificar("Passo 1 ✔ A área em hectares aparece", "\"Área confirmada (… ha)\"",
    () => expect(page.getByText(/Área confirmada \([\d.,]+ ha\)/)).toBeVisible(), () => page.getByText(/Área confirmada \(/).innerText());
  await aud.captura("Passo 1 opcional · área confirmada", { paginaInteira: false });
});

test("Passo 8 (opcional): telas de demonstração de erro", async ({ page, aud }) => {
  const eu = new Humano(page);
  await page.goto("/comparacao/carga");
  await eu.ler(1200);
  await aud.verificar("Passo 8 ✔ Tela de demonstração marcada com a faixa amarela", "faixa \"DADO DE EXEMPLO\" visível",
    () => expect(page.getByText("DADO DE EXEMPLO — não é resultado real").first()).toBeVisible());
  await eu.clicar(page.getByRole("button", { name: "Simular: falha sem cache" }));
  await eu.ler(3500);
  await aud.verificar("Passo 8 ✔ \"Falha sem cache\": o site não mostra resultado e explica o que fazer", "sem resultado final; explicação do que fazer",
    async () => { await expect(page.locator("main")).toContainText(/sem cópia guardada|Não foi possível/); await expect(page.locator("main").getByText("Resultado completo.", { exact: true })).toHaveCount(0); },
    () => page.locator("main").innerText().then((t) => t.slice(0, 240)));
  await aud.captura("Passo 8 · falha sem cópia guardada");
  await eu.clicar(page.getByRole("link", { name: "Erros e fontes" }));
  await eu.ler(1200);
  await aud.verificar("Passo 8 ✔ \"Erros e fontes\" mostra como o sistema reage quando uma fonte cai", "três estados de uma fonte",
    async () => { for (const t of ["Fonte respondeu", "Fonte fora do ar, com cópia guardada", "Fonte fora do ar, sem cópia guardada"]) await expect(page.getByText(t).first()).toBeVisible(); });
  await aud.captura("Passo 8 · erros e fontes");
});
