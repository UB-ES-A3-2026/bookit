import { test, expect } from "@playwright/test";

// Tests E2E del cercador de la pàgina d'inici (US4-T7).
// La pàgina de resultats amb les dades de l'API és la US4-T8; aquí només es comprova que el cercador hi porta.

const campCerca = (page) => page.getByRole("searchbox", { name: "Cerca llibres per títol, autor o ISBN" });
const botoCercar = (page) => page.getByRole("button", { name: "Buscar llibres" });

test("el cercador es veu a la pàgina d'inici", async ({ page }) => {
  await page.goto("/");

  await expect(campCerca(page)).toBeVisible();
  await expect(campCerca(page)).toHaveAttribute("placeholder", "Quin llibre busques?");
  await expect(botoCercar(page)).toBeVisible();
});

test("cercar amb el botó porta als resultats amb el text cercat", async ({ page }) => {
  await page.goto("/");

  await campCerca(page).fill("  La plaça del Diamant  ");
  await botoCercar(page).click();

  await expect(page).toHaveURL("/cerca?q=La+pla%C3%A7a+del+Diamant");
  await expect(page.getByRole("heading", { name: "Resultats de la cerca" })).toBeVisible();
  await expect(page.getByText("Has cercat «La plaça del Diamant».")).toBeVisible();
});

test("cercar amb la tecla Enter també porta als resultats", async ({ page }) => {
  await page.goto("/");

  await campCerca(page).fill("Mercè Rodoreda");
  await campCerca(page).press("Enter");

  await expect(page).toHaveURL("/cerca?q=Merc%C3%A8+Rodoreda");
});

for (const text of ["", "   "]) {
  test(`amb el camp ${text ? "amb només espais" : "buit"} no es cerca res`, async ({ page }) => {
    await page.goto("/");

    await campCerca(page).fill(text);
    await botoCercar(page).click();

    await expect(page).toHaveURL("/");
    await expect(campCerca(page)).toBeFocused();
  });
}

test.describe("en mòbil", () => {
  test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

  test("el cercador cap a la pantalla sense desplaçament horitzontal", async ({ page }) => {
    await page.goto("/");

    await expect(botoCercar(page)).toBeInViewport({ ratio: 1 });
    const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(ampladaPagina).toBeLessThanOrEqual(375);
  });
});
