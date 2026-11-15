// Bateria de testes de ponta a ponta auditável (Playwright). Capturas e relatório em docs/testes-e2e/.
// Uso (na pasta frontend): npx playwright test   (sobe API e site se não estiverem rodando)
// Navegador: o Microsoft Edge instalado no computador (channel "msedge"), sem baixar navegador.
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /.*\.e2e\.ts$/, // .e2e.ts para o vitest não pegar estes arquivos
  fullyParallel: false,
  workers: 1, // ordem fixa: o relatório lê de cima para baixo como um roteiro
  retries: 0, // auditoria: uma falha aparece como falha, sem nova tentativa escondida
  timeout: 300_000,
  expect: { timeout: 20_000 },
  reporter: [["list"], ["json", { outputFile: "test-results/resultado.json" }]],
  globalSetup: "./e2e/preparar.ts",
  globalTeardown: "./e2e/relatorio.ts",
  use: {
    channel: "msedge",
    baseURL: "http://localhost:4321",
    viewport: { width: 1280, height: 900 },
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run --project ../backend uvicorn tellus.api.app:app --port 8000",
      url: "http://localhost:8000/api/contrato/versao",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npx astro dev --port 4321",
      url: "http://localhost:4321",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
