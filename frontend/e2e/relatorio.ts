// Depois da bateria: junta os registros de cada teste em docs/testes-e2e/RELATORIO.md (gerado; não editar à mão).
import fs from "node:fs";
import path from "node:path";
import { DIR_DOCS, DIR_REGISTRO, type Registro } from "./auditoria";

const TITULO_SUITE: Record<string, string> = {
  "01-tela-inicial": "1. Tela inicial e escolha do local",
  "02-entradas": "2. Entradas e validação",
  "03-calculo-real": "3. Cálculo real (Rio Verde-GO)",
  "04-premissas": "4. Premissas editadas e recálculo",
  "05-idioma": "5. Versão em inglês (spec 014)",
  "06-celular": "6. Celular (390 × 844)",
  "07-erros-simulados": "7. Telas de erro simuladas",
  "08-api": "8. API do contrato",
};
const ICONE: Record<string, string> = { passed: "✅ passou", failed: "❌ falhou", timedOut: "⏱️ tempo esgotado", skipped: "⏭️ pulado", interrupted: "⛔ interrompido" };
const rotulo = (r: Registro) => r.esperado === "failed" && r.status === "failed"
  ? "⚠️ defeito conhecido (falhou como esperado)" : r.esperado === "failed" && r.status === "passed"
  ? "❗ defeito corrigido? (passou; tirar a marca test.fail)" : ICONE[r.status ?? ""] ?? r.status ?? "—";
const conforme = (r: Registro) => r.status === r.esperado;
const cel = (s: string) => s.replace(/\|/g, "\\|").replace(/\n/g, " ");
const hora = (iso: string) => new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });

export default async function relatorio(): Promise<void> {
  if (!fs.existsSync(DIR_REGISTRO)) return;
  const meta = JSON.parse(fs.readFileSync(path.join(DIR_REGISTRO, "_meta.json"), "utf-8"));
  const regs: Registro[] = fs.readdirSync(DIR_REGISTRO).filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(DIR_REGISTRO, f), "utf-8")))
    .sort((a, b) => a.suite.localeCompare(b.suite) || a.inicio.localeCompare(b.inicio));
  const verifs = regs.flatMap((r) => r.etapas.flatMap((e) => e.verificacoes));
  const capturas = regs.flatMap((r) => r.etapas.filter((e) => e.captura)).length;
  const passaram = regs.filter(conforme).length;
  const defeitos = regs.filter((r) => r.esperado === "failed");
  const navegador = regs.find((r) => r.navegador)?.navegador ?? "—";

  const l: string[] = [];
  l.push("# Relatório da bateria de testes de ponta a ponta", "");
  l.push("> Gerado automaticamente por `frontend/e2e/relatorio.ts` ao fim de `npx playwright test`. Não editar à mão:", "> rode a bateria de novo para atualizar. Como rodar e o que cada suíte cobre: [README.md](README.md).", "");
  l.push("## Resumo", "");
  l.push(`| Item | Valor |`, `|---|---|`);
  l.push(`| Resultado | **${passaram} de ${regs.length} testes conforme o esperado** ${defeitos.length ? ` (${defeitos.length} deles são defeitos conhecidos, abaixo)` : ", nenhum defeito conhecido"} |`);
  l.push(`| Verificações | ${verifs.filter((v) => v.ok).length} de ${verifs.length} atendidas${defeitos.length ? " (as não atendidas são as dos defeitos conhecidos)" : ""} |`);
  l.push(`| Capturas de tela | ${capturas} |`);
  l.push(`| Início da execução | ${hora(meta.inicio)} (horário de Brasília) |`);
  l.push(`| Commit testado | \`${meta.commit}\` (branch \`${meta.branch}\`${meta.alteracoes_locais ? `, com ${meta.alteracoes_locais} arquivo(s) alterado(s) fora do commit` : ", sem alterações locais"}) |`);
  l.push(`| Navegador | Microsoft Edge ${navegador} (Playwright ${meta.playwright}, Node ${meta.node}) |`);
  l.push(`| Contrato da API | ${meta.contrato_api} |`);
  l.push(`| Dados | API local com as séries e caches versionados do repositório (sem login NASA) |`, "");

  if (defeitos.length) {
    l.push("## Defeitos conhecidos encontrados pela bateria", "");
    l.push("Testes marcados com `test.fail`: descrevem o comportamento correto e falham enquanto o defeito existir.", "Quando o defeito for corrigido, o Playwright acusa \"passou inesperadamente\" e a marca deve sair.", "");
    for (const r of defeitos) l.push(`- [${cel(r.teste)}](#${ancora(r)}): ${r.defeito ?? ""} (\`${r.arquivo}\`)`);
    l.push("");
  }
  l.push("## Testes", "", "| Suíte | Teste | Resultado | Etapas | Verificações |", "|---|---|---|---|---|");
  for (const r of regs) {
    const v = r.etapas.flatMap((e) => e.verificacoes);
    l.push(`| ${TITULO_SUITE[r.suite] ?? r.suite} | [${cel(r.teste)}](#${ancora(r)}) | ${rotulo(r)} | ${r.etapas.length} | ${v.filter((x) => x.ok).length}/${v.length} |`);
  }
  l.push("");

  let suiteAtual = "";
  for (const r of regs) {
    if (r.suite !== suiteAtual) { suiteAtual = r.suite; l.push(`## ${TITULO_SUITE[r.suite] ?? r.suite}`, ""); }
    l.push(`<a id="${ancora(r)}"></a>`, `### ${r.teste}`, "");
    l.push(`${rotulo(r)} · arquivo \`${r.arquivo}\` · tela ${r.viewport ?? "—"} · ${hora(r.inicio)} → ${r.fim ? hora(r.fim) : "—"}`, "");
    if (r.defeito) l.push(`**Defeito conhecido:** ${r.defeito}`, "");
    if (r.erro) l.push(r.esperado === "failed" ? "**Falha registrada (esperada):**" : "**Erro:**", "", "```", r.erro, "```", "");
    for (const e of r.etapas) {
      l.push(`#### Etapa ${e.numero}: ${e.titulo}`, "");
      l.push(`URL: \`${e.url.replace("http://localhost:4321", "")}\``, "");
      if (e.verificacoes.length) {
        l.push("| | Verificação | Esperado | Obtido |", "|---|---|---|---|");
        for (const v of e.verificacoes) l.push(`| ${v.ok ? "✅" : "❌"} | ${cel(v.descricao)} | ${cel(v.esperado)} | ${cel(v.obtido)} |`);
        l.push("");
      }
      if (e.captura) l.push(`![${cel(e.titulo)}](capturas/${e.captura})`, "");
    }
  }
  fs.writeFileSync(path.join(DIR_DOCS, "RELATORIO.md"), l.join("\n"), "utf-8");
}

function ancora(r: Registro): string {
  return `${r.suite}-${r.teste}`.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
