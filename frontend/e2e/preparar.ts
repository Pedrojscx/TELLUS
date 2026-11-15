// Antes da bateria: limpa as capturas e evidências da execução anterior (o relatório reflete UMA execução)
// e guarda os metadados do ambiente (commit, versões) para o relatório.
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { API, DIR_CAPTURAS, DIR_EVIDENCIAS, DIR_REGISTRO } from "./auditoria";

const sh = (c: string) => { try { return execSync(c, { encoding: "utf-8" }).trim(); } catch { return "—"; } };

export default async function preparar(): Promise<void> {
  for (const d of [DIR_CAPTURAS, DIR_EVIDENCIAS, DIR_REGISTRO]) fs.rmSync(d, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); // Windows: arquivo aberto por outro programa
  fs.mkdirSync(DIR_REGISTRO, { recursive: true });
  const versao = await fetch(`${API}/api/contrato/versao`).then((r) => r.json()).catch(() => null);
  const meta = {
    inicio: new Date().toISOString(),
    commit: sh("git rev-parse --short HEAD"),
    branch: sh("git rev-parse --abbrev-ref HEAD"),
    alteracoes_locais: sh("git status --porcelain --untracked-files=no").split("\n").filter(Boolean).length,
    playwright: JSON.parse(fs.readFileSync(path.resolve("node_modules/@playwright/test/package.json"), "utf-8")).version,
    node: process.version,
    contrato_api: versao?.versao_contrato ?? "API fora do ar",
  };
  fs.writeFileSync(path.join(DIR_REGISTRO, "_meta.json"), JSON.stringify(meta, null, 1));
}
