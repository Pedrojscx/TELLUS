// Teste de usabilidade do caso de referência (#104, #56): o roteiro da equipe executado no ritmo de uma pessoa,
// com vídeo da sessão e captura de cada passo. Saída em docs/teste-usabilidade/.
// Uso (na pasta frontend): npm run test:usabilidade
import { defineConfig } from "@playwright/test";

process.env.E2E_SAIDA = "teste-usabilidade"; // pasta de docs/ usada pela fixture de auditoria (lida nos workers)

export default defineConfig({
  testDir: "./e2e/usabilidade",
  testMatch: /.*\.usab\.ts$/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 600_000,
  expect: { timeout: 30_000 },
  reporter: [["list"], ["json", { outputFile: "test-results/usabilidade.json" }]],
  globalSetup: "./e2e/preparar.ts",
  globalTeardown: "./e2e/usabilidade/relatorio.ts",
  outputDir: "test-results/usabilidade",
  use: {
    channel: "msedge",
    baseURL: "http://localhost:4321",
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    launchOptions: { slowMo: 120 }, // cada ação com um pequeno atraso, como uma pessoa
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "computador",
      testMatch: /computador\.usab\.ts$/,
      use: { viewport: { width: 1280, height: 800 }, video: { mode: "on", size: { width: 1280, height: 800 } } },
    },
    {
      name: "celular",
      testMatch: /celular\.usab\.ts$/,
      use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2,
             video: { mode: "on", size: { width: 390, height: 844 } } },
    },
  ],
  webServer: [
    { command: "uv run --project ../backend uvicorn tellus.api.app:app --port 8000", url: "http://localhost:8000/api/contrato/versao",
      reuseExistingServer: true, timeout: 120_000 },
    { command: "npx astro dev --port 4321", url: "http://localhost:4321", reuseExistingServer: true, timeout: 120_000 },
  ],
});
