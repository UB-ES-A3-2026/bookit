import { test, expect } from "@playwright/test";

// Tests E2E de navegació com a convidat (US0-T17).
// Cada test correspon a un cas de docs/casos-prova-us0.md. El CP-US0-06 (teclat) es prova a mà a la T18.

const botoRegistre = (page) => page.getByRole("link", { name: "Registra't" });

// Fins a US1-T7, la pantalla de registre és la pàgina provisional de US0-T13 amb el títol "Registre".
const titolRegistre = (page) => page.getByRole("heading", { name: "Registre" });

test("CP-US0-01 · un convidat obre la pàgina d'inici", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (missatge) => {
    if (missatge.type() === "error") errors.push(missatge.text());
  });

  await page.goto("/");

  await expect(page).toHaveURL("/");
  await expect(page.getByText("bookit.", { exact: true })).toBeVisible();
  await expect(botoRegistre(page)).toBeVisible();
  expect(errors).toEqual([]);
});

test("CP-US0-02 · clic a \"Registra't\" obre la pantalla de registre", async ({ page }) => {
  await page.goto("/");

  await botoRegistre(page).click();

  await expect(page).toHaveURL("/registre");
  await expect(titolRegistre(page)).toBeVisible();
});

test.describe("en mòbil", () => {
  test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

  test("CP-US0-03 · \"Registra't\" es veu sencer i porta al registre", async ({ page }) => {
    await page.goto("/");

    await expect(botoRegistre(page)).toBeInViewport({ ratio: 1 });
    const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(ampladaPagina).toBeLessThanOrEqual(375);

    await botoRegistre(page).tap();

    await expect(page).toHaveURL("/registre");
    await expect(titolRegistre(page)).toBeVisible();
  });
});

test("CP-US0-04 · tornar enrere des del registre", async ({ page }) => {
  await page.goto("/");
  await botoRegistre(page).click();
  await expect(page).toHaveURL("/registre");

  await page.goBack();

  await expect(page).toHaveURL("/");
  await expect(botoRegistre(page)).toBeVisible();
});

test("CP-US0-05 · obrir /registre directament o recarregar-la", async ({ page }) => {
  const resposta = await page.goto("/registre");

  expect(resposta.status()).toBe(200);
  await expect(titolRegistre(page)).toBeVisible();

  const respostaRecarrega = await page.reload();

  expect(respostaRecarrega.status()).toBe(200);
  await expect(titolRegistre(page)).toBeVisible();
});
