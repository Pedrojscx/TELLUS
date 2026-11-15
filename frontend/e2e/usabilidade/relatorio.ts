// Relatório do teste de usabilidade (docs/teste-usabilidade/RELATORIO.md), organizado pelos passos do roteiro.
// Copia os vídeos das sessões para docs/teste-usabilidade/videos/. Gerado; não editar à mão.
import fs from "node:fs";
import path from "node:path";
import { DIR_DOCS, DIR_REGISTRO, type Registro } from "../auditoria";

const PASSOS: Record<string, string> = {
  "1": "Tela inicial: escolher a lavoura",
  "2": "Entradas",
  "3": "Metodologia",
  "4": "Resultado (o cálculo de verdade)",
  "5": "Premissas: mudar valores e recalcular",
  "6": "Não deixar plantar fora do ZARC",
  "7": "Celular",
  "8": "Telas de demonstração (opcional)",
};
const cel = (s: string) => s.replace(/\|/g, "\\|").replace(/\n/g, " ");
const hora = (iso: string) => new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
const passoDe = (s: string) => s.match(/^Passo (\d)/)?.[1] ?? "?";

export default async function relatorio(): Promise<void> {
  if (!fs.existsSync(DIR_REGISTRO)) return;
  const meta = JSON.parse(fs.readFileSync(path.join(DIR_REGISTRO, "_meta.json"), "utf-8"));
  const regs: Registro[] = fs.readdirSync(DIR_REGISTRO).filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(DIR_REGISTRO, f), "utf-8")))
    .sort((a, b) => a.inicio.localeCompare(b.inicio));

  // vídeos
  const dirVideos = path.join(DIR_DOCS, "videos");
  fs.rmSync(dirVideos, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 });
  fs.mkdirSync(dirVideos, { recursive: true });
  const videos: { teste: string; arquivo: string }[] = [];
  // O Playwright move o vídeo para test-results/usabilidade/<arquivo>-<título>-<projeto>/video.webm ao fechar a página.
  const dirSaida = path.resolve(DIR_REGISTRO, "..", "usabilidade");
  const pastas = fs.existsSync(dirSaida) ? fs.readdirSync(dirSaida) : [];
  regs.forEach((r, i) => {
    const chave = `${r.suite}-${r.teste.replace(/[^\p{L}\p{N}]+/gu, "-").slice(0, 7)}`;
    const pasta = pastas.find((p) => p.startsWith(chave) && fs.existsSync(path.join(dirSaida, p, "video.webm")));
    if (!pasta) return;
    const nome = `${String(i + 1).padStart(2, "0")}-${r.suite.replace(/\.usab\.ts$/, "")}-${r.teste.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40).replace(/-$/, "")}.webm`;
    fs.copyFileSync(path.join(dirSaida, pasta, "video.webm"), path.join(dirVideos, nome));
    videos.push({ teste: r.teste, arquivo: `videos/${nome}` });
  });

  const itens = regs.flatMap((r) => r.etapas.flatMap((e) => e.verificacoes));
  const ok = itens.filter((v) => v.ok).length;
  const todos = regs.every((r) => r.status === "passed");
  const duracao = regs.reduce((s, r) => s + (r.fim ? Date.parse(r.fim) - Date.parse(r.inicio) : 0), 0);
  const navegador = regs.find((r) => r.navegador)?.navegador ?? "—";

  const l: string[] = [];
  l.push("# Teste de usabilidade do caso de referência (#104, #56)", "");
  l.push("> Gerado por `frontend/e2e/usabilidade/relatorio.ts` ao fim de `npm run test:usabilidade`. Não editar à mão.", "");
  l.push("## Parecer", "");
  l.push(todos
    ? `**Passou.** Os ${ok} itens ✔ do roteiro de teste foram atendidos, no computador e no celular. O produtor consegue ir da tela inicial ao resultado do caso de referência (Rio Verde-GO, colheita 20/01/2027, solo argiloso, grupo "não sei"), editar premissas e ver o efeito, sem nenhuma alternativa fora do ZARC.`
    : `**Não passou.** ${ok} de ${itens.length} itens do roteiro atendidos. Os itens ✘ e as capturas abaixo mostram onde a sessão parou.`, "");
  l.push("## Como o teste foi feito", "");
  l.push("- O roteiro de teste da equipe (passos 1 a 8) foi executado no navegador por um agente que age como uma pessoa:",
    "  digita letra por letra, passa o mouse antes de clicar, rola a página e pausa para ler. Nada é preenchido por código.",
    "- Cada \"✔\" do roteiro virou um item verificado, com o que se esperava e o que apareceu na tela.",
    "- Cada sessão foi gravada em vídeo, e cada passo tem captura de tela.",
    "- Limite: não é um teste com produtores reais. O critério SC-001 da spec 012 (5 de 5 participantes) pede pessoas; este",
    "  teste confere que o fluxo do roteiro funciona do começo ao fim, como a equipe combinou para a #104.", "");
  l.push("| Item | Valor |", "|---|---|");
  l.push(`| Data | ${hora(meta.inicio)} (horário de Brasília) |`);
  l.push(`| Itens do roteiro | ${ok} de ${itens.length} ✔ |`);
  l.push(`| Sessões | ${regs.map((r) => `${r.teste} (${r.viewport}, ${r.status === "passed" ? "passou" : "falhou"})`).join("; ")} |`);
  l.push(`| Duração total | ${Math.round(duracao / 1000)} s |`);
  l.push(`| Commit testado | \`${meta.commit}\` (${meta.alteracoes_locais ? `${meta.alteracoes_locais} arquivo(s) alterado(s) fora do commit` : "sem alterações locais"}) |`);
  l.push(`| Navegador | Microsoft Edge ${navegador} (Playwright ${meta.playwright}) |`);
  l.push(`| API | contrato ${meta.contrato_api}, local, com as séries e caches versionados do repositório |`, "");
  if (videos.length) {
    l.push("## Vídeos das sessões", "");
    for (const v of videos) l.push(`- [${cel(v.teste)}](${v.arquivo})`);
    l.push("");
  }

  for (const [n, titulo] of Object.entries(PASSOS)) {
    const vs = itens.filter((v) => passoDe(v.descricao) === n);
    const caps = regs.flatMap((r) => r.etapas.filter((e) => e.captura && passoDe(e.titulo) === n));
    if (!vs.length && !caps.length) continue;
    l.push(`## Passo ${n}: ${titulo}`, "");
    if (vs.length) {
      l.push("| | O que o roteiro pede | O que apareceu |", "|---|---|---|");
      for (const v of vs) l.push(`| ${v.ok ? "✔" : "✘"} | ${cel(v.descricao.replace(/^Passo \d ✔ /, ""))} | ${cel(v.obtido === "conforme o esperado" ? v.esperado : v.obtido)} |`);
      l.push("");
    }
    for (const e of caps) l.push(`**${cel(e.titulo.replace(/^Passo [\w ]+ · /, ""))}**`, "", `![${cel(e.titulo)}](capturas/${e.captura})`, "");
  }
  const erros = regs.filter((r) => r.erro);
  if (erros.length) {
    l.push("## Falhas", "");
    for (const r of erros) l.push(`- **${cel(r.teste)}**: \`${cel(r.erro ?? "")}\``);
    l.push("");
  }
  fs.writeFileSync(path.join(DIR_DOCS, "RELATORIO.md"), l.join("\n"), "utf-8");
}
