import { test, expect } from "@playwright/test";

// Tests E2E del tipus de lliurament (US7-T6).
// Les respostes es simulen amb page.route perquè no hi ha una fixture E2E
// estable amb llibres, comanda i tarifes configurades.

const URL_COSTOS = "**/api/prestecs/comandes/cost-enviament/";
const URL_COMANDA = "**/api/prestecs/comandes/";

async function prepararComanda(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: "refresh-e2e-usuari",
        usuari: {
          id: 25,
          nom: "Usuari E2E",
          correu: "usuari.e2e@example.com",
          rol: "usuari",
          address: "C/ de la Muntanya 12, 08035 Barcelona",
        },
        rol: "usuari",
      }),
    );
    sessionStorage.setItem(
      "bookit.comanda",
      JSON.stringify([
        {
          id: 7,
          titol: "La plaça del Diamant",
          autor: "Mercè Rodoreda",
          portada: "",
          biblioteca: { id: 3, nom: "Biblioteca Montbau" },
        },
        {
          id: 9,
          titol: "Solitud",
          autor: "Víctor Català",
          portada: "",
          biblioteca: { id: 3, nom: "Biblioteca Montbau" },
        },
      ]),
    );
  });
}

async function obrirComanda(page) {
  await page.route(URL_COSTOS, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ domicili: "2.50", recollida: "0.00" }),
    });
  });
  await page.goto("/comanda");
  await expect(page.getByRole("heading", { name: "Tipus de lliurament", exact: true })).toBeVisible();
}

async function triarRecollida(page) {
  await page.getByRole("radio", { name: /Recollida a la biblioteca/ }).check();
}

test.describe("tipus de lliurament (US7)", () => {
  test("CP-US7-01 · mostra el cost de domicili abans de confirmar", async ({ page }) => {
    await prepararComanda(page);
    await obrirComanda(page);

    await expect(page.getByRole("radio", { name: /Lliurament a domicili/ })).toBeChecked();
    await expect(page.getByRole("radio", { name: /Lliurament a domicili/ }).locator("xpath=..").getByText("2,50 €", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Adreça de lliurament", { exact: true })).toHaveValue(
      "C/ de la Muntanya 12, 08035 Barcelona",
    );
  });

  test("CP-US7-02 · recollida mostra cost zero i envia el tipus corresponent", async ({ page }) => {
    await prepararComanda(page);
    await obrirComanda(page);

    await triarRecollida(page);

    await expect(page.getByRole("radio", { name: /Recollida a la biblioteca/ }).locator("xpath=..").getByText("0,00 €", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Adreça de lliurament", { exact: true })).toHaveCount(0);

    let cosEnviat;
    await page.route(URL_COMANDA, async (ruta) => {
      cosEnviat = ruta.request().postDataJSON();
      await ruta.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ id: 12, estat: "rebuda", tipus_lliurament: "recollida", cost_enviament: "0.00" }),
      });
    });

    await page.getByRole("button", { name: "Confirmar comanda", exact: true }).click();

    expect(cosEnviat).toEqual({
      biblioteca: 3,
      llibres: [7, 9],
      tipus_lliurament: "recollida",
      adreca_lliurament: "",
    });
  });

  test("CP-US7-04 · envia una adreça alternativa per a domicili", async ({ page }) => {
    await prepararComanda(page);
    await obrirComanda(page);

    await page.getByLabel("Adreça de lliurament", { exact: true }).fill(
      "C/ de Provença 123, 08029 Barcelona",
    );

    let cosEnviat;
    await page.route(URL_COMANDA, async (ruta) => {
      cosEnviat = ruta.request().postDataJSON();
      await ruta.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ id: 12, estat: "rebuda", tipus_lliurament: "domicili", cost_enviament: "2.50" }),
      });
    });

    await page.getByRole("button", { name: "Confirmar comanda", exact: true }).click();

    expect(cosEnviat).toEqual({
      biblioteca: 3,
      llibres: [7, 9],
      tipus_lliurament: "domicili",
      adreca_lliurament: "C/ de Provença 123, 08029 Barcelona",
    });
  });

  test("CP-US7-06 · impedeix domicili sense adreça", async ({ page }) => {
    await prepararComanda(page);
    await obrirComanda(page);

    await page.getByLabel("Adreça de lliurament", { exact: true }).fill("");
    await page.getByRole("button", { name: "Confirmar comanda", exact: true }).click();

    await expect(page.getByRole("alert").getByText("Indica l'adreça de lliurament.", { exact: true })).toBeVisible();
  });

  test("mostra un error si no es poden carregar els costos", async ({ page }) => {
    await prepararComanda(page);
    await page.addInitScript(() => {});
    await page.route(URL_COSTOS, async (ruta) => {
      await ruta.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Error intern." }),
      });
    });

    await page.goto("/comanda");

    await expect(page.getByRole("alert").getByText("No s'han pogut carregar els costos d'enviament.", { exact: true })).toBeVisible();
  });
});
