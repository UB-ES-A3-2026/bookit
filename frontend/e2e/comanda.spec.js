import { test, expect } from "@playwright/test";

// Tests E2E de la comanda amb diversos llibres (US6-T10).
// Els resultats i la confirmació es simulen amb page.route perquè no hi ha
// una fixture E2E estable amb catàlegs, biblioteques i estoc.

const URL_CERCA = "**/api/cataleg/llibres/**";
const URL_COMANDA = "**/api/prestecs/comandes/";
const URL_COSTOS = "**/api/prestecs/comandes/cost-enviament/";
const URL_NOTIFICACIONS = "**/api/prestecs/notificacions/";

async function entrarComUsuari(page) {
  // La capçalera demana les notificacions (US8) i la comanda, el cost d'enviament (US7).
  // Amb el token de prova el backend respondria 401 i es tancaria la sessió.
  await page.route(URL_NOTIFICACIONS, (ruta) =>
    ruta.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
  );
  await page.route(URL_COSTOS, (ruta) =>
    ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ domicili: "2.50", recollida: "0.00" }),
    }),
  );
  await page.addInitScript(() => {
    sessionStorage.removeItem("bookit.comanda");
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: "refresh-e2e-usuari",
        usuari: {
          id: 25,
          nom: "Usuari E2E",
          correu: "usuari.e2e@example.com",
          adreca: "C/ Major 1",
          rol: "usuari",
        },
        rol: "usuari",
      }),
    );
  });
}

function llibre({ id, titol, disponible = true }) {
  return {
    id,
    titol,
    autor: `Autor ${id}`,
    portada: "",
    disponible,
    mitjana_valoracions: null,
    nombre_valoracions: 0,
    biblioteca: disponible ? { id: 3, nom: "Biblioteca Montbau" } : null,
  };
}

async function obrirCerca(page, llibres) {
  await page.route(URL_CERCA, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        count: llibres.length,
        next: null,
        previous: null,
        results: llibres,
      }),
    });
  });
  await page.goto("/cerca?q=llibre");
  await expect(page.getByRole("heading", { name: "Resultats de la cerca", exact: true })).toBeVisible();
}

function targeta(page, titol) {
  return page
    .getByRole("list", { name: "Resultats de la cerca" })
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: titol, exact: true }) });
}

test.describe("comanda amb diversos llibres (US6)", () => {
  test("CP-US6-01 · afegeix diversos llibres i confirma la comanda", async ({ page }) => {
    await entrarComUsuari(page);
    await obrirCerca(page, [
      llibre({ id: 7, titol: "Solitud" }),
      llibre({ id: 9, titol: "La plaça del Diamant" }),
    ]);

    await targeta(page, "Solitud").getByRole("button", { name: "Afegir a la comanda", exact: true }).click();
    await targeta(page, "La plaça del Diamant").getByRole("button", { name: "Afegir a la comanda", exact: true }).click();

    await page.getByRole("link", { name: "La meva comanda (2)", exact: true }).click();

    await expect(page).toHaveURL("/comanda");
    await expect(page.getByRole("heading", { name: "Solitud", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "La plaça del Diamant", exact: true })).toBeVisible();

    let cosEnviat;
    await page.route(URL_COMANDA, async (ruta) => {
      cosEnviat = ruta.request().postDataJSON();
      await ruta.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ id: 12, estat: "rebuda", llibres: [] }),
      });
    });

    await page.getByRole("button", { name: "Confirmar comanda", exact: true }).click();

    await expect(page.getByText("Encara no has afegit cap llibre a la comanda.", { exact: true })).toBeVisible();
    expect(cosEnviat).toEqual({
      biblioteca: 3,
      llibres: [7, 9],
      tipus_lliurament: "domicili",
      adreca_lliurament: "C/ Major 1",
    });
  });

  test("CP-US6-09 · impedeix confirmar quan se supera el límit", async ({ page }) => {
    await entrarComUsuari(page);
    await page.addInitScript(() => {
      sessionStorage.setItem("bookit.comanda", JSON.stringify([
        { id: 1, titol: "Llibre 1", autor: "Autor 1", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
        { id: 2, titol: "Llibre 2", autor: "Autor 2", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
        { id: 3, titol: "Llibre 3", autor: "Autor 3", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
        { id: 4, titol: "Llibre 4", autor: "Autor 4", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
        { id: 5, titol: "Llibre 5", autor: "Autor 5", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
        { id: 6, titol: "Llibre 6", autor: "Autor 6", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
      ]));
    });

    await page.goto("/comanda");

    await expect(page.getByText("Has superat el límit de llibres per aquesta comanda, elimina un per continuar", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Confirmar comanda", exact: true })).toBeDisabled();
  });

  test("CP-US6-10 · no permet afegir un llibre sense estoc i ofereix l'espera", async ({ page }) => {
    await entrarComUsuari(page);
    await obrirCerca(page, [llibre({ id: 9, titol: "Solitud sense estoc", disponible: false })]);

    const senseEstoc = targeta(page, "Solitud sense estoc");
    await expect(senseEstoc.getByText(/Aquest llibre no te estoc en aquest moment/)).toBeVisible();
    await expect(senseEstoc.getByRole("button", { name: "No disponible", exact: true })).toBeDisabled();

    await senseEstoc.getByRole("button", { name: "Apuntar-me a la llista d'espera", exact: true }).click();
    await expect(senseEstoc.getByRole("button", { name: "Apuntat a la llista d'espera", exact: true })).toBeDisabled();
  });

  test("CP-US6-10 · mostra estoc rebutjat en confirmar i permet apuntar-s'hi", async ({ page }) => {
    await entrarComUsuari(page);
    await page.addInitScript(() => {
      sessionStorage.setItem("bookit.comanda", JSON.stringify([
        { id: 9, titol: "Solitud", autor: "Víctor Català", biblioteca: { id: 3, nom: "Biblioteca Montbau" } },
      ]));
    });

    await page.route(URL_COMANDA, async (ruta) => {
      await ruta.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          llibres: ["Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera"],
          sense_estoc: [9],
        }),
      });
    });

    await page.goto("/comanda");
    await page.getByRole("button", { name: "Confirmar comanda", exact: true }).click();

    await expect(page.getByRole("alert").getByText("Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Apuntar-me a la llista d'espera", exact: true }).click();
    await expect(page.getByRole("button", { name: "Apuntat a la llista d'espera", exact: true })).toBeDisabled();
  });

  test("redirigeix un usuari sense sessió quan obre la comanda", async ({ page }) => {
    await page.goto("/comanda");
    await expect(page).toHaveURL("/inicia-sessio");
  });
});
