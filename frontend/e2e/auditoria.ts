// Fixture de auditoria: cada etapa vira uma captura de tela numerada + o registro do que foi verificado.
// O registro (JSON por teste) é lido por relatorio.ts, que monta docs/testes-e2e/RELATORIO.md.
import { test as base, expect, type Page, type TestInfo } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
// Saída: docs/testes-e2e (bateria técnica) ou outra pasta de docs/ definida pela config (E2E_SAIDA, ex.: teste-usabilidade).
const SAIDA = process.env.E2E_SAIDA ?? "testes-e2e";
export const DIR_DOCS = path.resolve(AQUI, "../../docs", SAIDA);
export const DIR_CAPTURAS = path.join(DIR_DOCS, "capturas");
export const DIR_EVIDENCIAS = path.join(DIR_DOCS, "evidencias");
export const DIR_REGISTRO = path.resolve(AQUI, "../test-results", `auditoria-${SAIDA}`);
export const API = "http://localhost:8000";

export interface Verificacao { descricao: string; esperado: string; obtido: string; ok: boolean }
export interface Etapa { numero: number; titulo: string; captura: string | null; verificacoes: Verificacao[]; url: string; quando: string }
export interface Registro {
  suite: string; teste: string; arquivo: string; inicio: string; fim?: string; status?: string; esperado?: string; erro?: string;
  defeito?: string; video?: string;
  navegador?: string; viewport?: string; etapas: Etapa[];
}

const slug = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
  .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);

export class Auditoria {
  private reg: Registro;
  private pendentes: Verificacao[] = [];
  private n = 0;
  readonly pasta: string;

  constructor(private page: Page, private info: TestInfo) {
    const suite = path.basename(info.file).replace(/\.e2e\.ts$/, "");
    this.pasta = path.join(suite, slug(info.title));
    this.reg = { suite, teste: info.title, arquivo: `frontend/e2e/${path.basename(info.file)}`,
                 inicio: new Date().toISOString(), etapas: [] };
  }

  /** Registra uma verificação. Se falhar, o registro guarda o que apareceu e a falha segue para o Playwright. */
  async verificar(descricao: string, esperado: string, checar: () => Promise<unknown>, obtido?: () => Promise<string>): Promise<void> {
    try {
      const r = await checar();
      const o = obtido ? await obtido() : typeof r === "string" ? r : "conforme o esperado";
      this.pendentes.push({ descricao, esperado, obtido: o, ok: true });
    } catch (e) {
      const o = obtido ? await obtido().catch(() => "—") : String((e as Error).message ?? e).split("\n")[0];
      this.pendentes.push({ descricao, esperado, obtido: o, ok: false });
      await this.captura("FALHA " + descricao);
      throw e;
    }
  }

  /** Fecha uma etapa: captura de tela inteira com as verificações feitas desde a etapa anterior. */
  async captura(titulo: string, opcoes: { paginaInteira?: boolean } = {}): Promise<void> {
    this.n += 1;
    const nome = `${String(this.n).padStart(2, "0")}-${slug(titulo)}.png`;
    const rel = path.join(this.pasta, nome);
    const destino = path.join(DIR_CAPTURAS, rel);
    fs.mkdirSync(path.dirname(destino), { recursive: true });
    let captura: string | null = rel.replace(/\\/g, "/");
    try {
      await this.page.screenshot({ path: destino, fullPage: opcoes.paginaInteira ?? true, animations: "disabled",
                                   style: "astro-dev-toolbar { display: none !important; }" }); // barra do modo dev do Astro
    } catch {
      captura = null; // página fechada ou navegação em curso: a etapa fica registrada sem imagem
    }
    this.reg.etapas.push({ numero: this.n, titulo, captura, verificacoes: this.pendentes, url: this.page.url(),
                           quando: new Date().toISOString() });
    this.pendentes = [];
  }

  /** Grava um arquivo de evidência (ex.: resposta da API) em docs/testes-e2e/evidencias/. */
  evidencia(nome: string, conteudo: unknown): string {
    const destino = path.join(DIR_EVIDENCIAS, this.reg.suite, nome);
    fs.mkdirSync(path.dirname(destino), { recursive: true });
    fs.writeFileSync(destino, typeof conteudo === "string" ? conteudo : JSON.stringify(conteudo, null, 1), "utf-8");
    return path.relative(DIR_DOCS, destino).replace(/\\/g, "/");
  }

  async finalizar(): Promise<void> {
    if (this.pendentes.length) await this.captura("verificações finais");
    const vp = this.page.viewportSize();
    Object.assign(this.reg, {
      fim: new Date().toISOString(), status: this.info.status, esperado: this.info.expectedStatus,
      defeito: this.info.annotations.find((a) => a.type === "fail")?.description, navegador: this.page.context().browser()?.version(),
      viewport: vp ? `${vp.width}×${vp.height}` : undefined,
      video: await this.page.video()?.path().catch(() => undefined),
      erro: this.info.error?.message?.split("\n").slice(0, 3).join(" ").replace(/\u001b\[[0-9;]*m/g, ""),
    });
    fs.mkdirSync(DIR_REGISTRO, { recursive: true });
    fs.writeFileSync(path.join(DIR_REGISTRO, `${this.reg.suite}--${slug(this.reg.teste)}.json`), JSON.stringify(this.reg, null, 1));
  }
}

export const test = base.extend<{ aud: Auditoria }>({
  aud: async ({ page }, use, info) => {
    const a = new Auditoria(page, info);
    await use(a);
    await a.finalizar();
  },
});
export { expect };
