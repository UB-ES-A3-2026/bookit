import { test, expect } from "@playwright/test";

// Tests E2E de biblioteques amb estoc i llista d'espera (US5-T12).
// Les respostes es simulen amb page.route perquè no hi ha fixtures E2E de
// biblioteques, coordenades i exemplars controlats.

const URL_DETALL = "**/api/cataleg/llibres/7/";
const URL_BIBLIOTEQUES = "**/api/cataleg/llibres/7/biblioteques/";
const URL_ESPERA = "**/api/cataleg/llibres/7/llista-espera/";

async function entrarComUsuari(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: "refresh-e2e-usuari",
        usuari: { id: 25, nom: "Usuari E2E", rol: "usuari" },
        rol: "usuari",
      }),
    );
  });
}

async function simularDetall(page) {
  await page.route(URL_DETALL, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        isbn: "9781234567890",
        portada: "",
      }),
    });
  });
}

async function obrirDetall(page) {
  await page.goto("/llibres/7?titol=La%20pla%C3%A7a%20del%20Diamant&autor=Merc%C3%A8%20Rodoreda");
  await expect(page.getByRole("heading", { name: "La plaça del Diamant", exact: true })).toBeVisible();
}

test.describe("biblioteques amb estoc (US5)", () => {
  test("CP-US5-01 i CP-US5-02 · mostra biblioteques i estoc ordenats", async ({ page }) => {
    await entrarComUsuari(page);
    await simularDetall(page);
    await page.route(URL_BIBLIOTEQUES, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          biblioteques: [
            { id: 3, nom: "Biblioteca Montbau", carrer: "Carrer 1", numero_porta: "10", exemplars: 2, distancia_km: 1.2 },
            { id: 4, nom: "Biblioteca Gràcia", carrer: "Carrer 2", numero_porta: "20", exemplars: 4, distancia_km: 3.8 },
          ],
          ordenada_per_distancia: true,
          missatge: null,
        }),
      });
    });

    await obrirDetall(page);

    await expect(page.getByRole("heading", { name: "Biblioteques amb estoc", exact: true })).toBeVisible();
    await expect(page.getByText("Ordenades per distància a la teva adreça predeterminada.", { exact: true })).toBeVisible();

    const llista = page.getByRole("list", { name: "Biblioteques que tenen el llibre en estoc" });
    await expect(llista.getByRole("heading", { level: 3 })).toHaveText(["Biblioteca Montbau", "Biblioteca Gràcia"]);
    await expect(page.getByText("2 exemplars disponibles", { exact: true })).toBeVisible();
    await expect(page.getByText("4 exemplars disponibles", { exact: true })).toBeVisible();
  });

  test("CP-US5-03 i CP-US5-06 · sense estoc ofereix la llista d'espera", async ({ page }) => {
    await entrarComUsuari(page);
    await simularDetall(page);
    await page.route(URL_BIBLIOTEQUES, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          biblioteques: [],
          ordenada_per_distancia: true,
          missatge: "Cap biblioteca te aquest llibre en estoc",
        }),
      });
    });
    await page.route(URL_ESPERA, async (ruta) => {
      await ruta.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ ja_apuntat: false, estat: "actiu" }),
      });
    });

    await obrirDetall(page);

    await expect(page.getByText("Cap biblioteca te aquest llibre en estoc", { exact: true })).toBeVisible();
    await expect(page.getByText("Aquest llibre no té estoc disponible.", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Llista d'espera", exact: true }).click();

    await expect(page.getByText("T'has apuntat a la llista d'espera d'aquest llibre.", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sol·licitud registrada", exact: true })).toBeDisabled();
  });

  test("CP-US5-05 · el convidat no rebrà l'ordre per distància", async ({ page }) => {
    await simularDetall(page);
    await page.route(URL_BIBLIOTEQUES, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          biblioteques: [
            { id: 3, nom: "Biblioteca Montbau", carrer: "Carrer 1", numero_porta: "10", exemplars: 2 },
          ],
          ordenada_per_distancia: false,
          missatge: "Registrat per ordenar les biblioteques per distància",
        }),
      });
    });

    await obrirDetall(page);

    await expect(page.getByText("Registrat per ordenar les biblioteques per distància", { exact: true })).toBeVisible();
    await expect(page.getByText("Biblioteca Montbau", { exact: true })).toBeVisible();
    await expect(page.getByText("2 exemplars disponibles", { exact: true })).toBeVisible();
  });
});
