import { defineConfig, devices } from "@playwright/test";

// Configuració dels tests E2E amb Playwright. Els tests són a la carpeta e2e/.
// https://playwright.dev/docs/test-configuration
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  // A la CI falla si algú ha deixat un test.only al codi.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  // "Desktop Chrome" fa servir la mida d'escriptori dels casos de prova (1280 × 720).
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Aixeca el servidor de Vite si no n'hi ha cap al port 5173 (fora de la CI reaprofita el de Docker o el d'npm run dev).
  webServer: {
    command: "npm run dev -- --strictPort",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
