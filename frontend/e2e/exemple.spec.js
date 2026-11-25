import { test, expect } from "@playwright/test";

// Test d'exemple: comprova que Playwright obre l'aplicació i que Vue la munta.
test("l'aplicació es carrega a la pàgina d'inici", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("#app")).not.toBeEmpty();
});
