import { expect, test } from "@playwright/test";

test("cada vista té el seu títol de pestanya i el favicon de bookit", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Inici · bookit");
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute("href", "/favicon.png");

  const favicon = await page.request.get("/favicon.png");
  expect(favicon.ok()).toBe(true);
  expect(favicon.headers()["content-type"]).toContain("image/png");

  await page.goto("/registre");
  await expect(page).toHaveTitle("Crear un compte · bookit");

  await page.goto("/inicia-sessio");
  await expect(page).toHaveTitle("Inicia sessió · bookit");
});

test("una ruta protegida redirigeix i mostra el títol de la vista final", async ({ page }) => {
  await page.goto("/cataleg");
  await expect(page).toHaveURL(/\/inicia-sessio$/);
  await expect(page).toHaveTitle("Inicia sessió · bookit");
});
