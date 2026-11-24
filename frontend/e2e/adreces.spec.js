import { test, expect } from "@playwright/test";

// Tests E2E de les adreces de lliurament (US3-T11).
// Les respostes es simulen amb page.route perquè l'entorn E2E no té una
// fixture estable amb un usuari i les seves adreces.

const URL_ADRECES = "**/api/usuaris/adreces/**";

async function entrarComUsuari(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: "refresh-e2e-usuari",
        usuari: { id: 1, nom: "Usuari E2E", correu: "usuari.e2e@example.com", rol: "usuari" },
        rol: "usuari",
      }),
    );
  });
}

function adreca({ id = 1, predeterminada = true } = {}) {
  return {
    id,
    municipi: "Barcelona",
    carrer: "Carrer Major 1",
    pis: "2n A",
    codi_postal: "08001",
    predeterminada,
  };
}

async function obrirAdreces(page) {
  await page.goto("/adreces");
  await expect(
    page.getByRole("heading", { name: "Les meves adreces de lliurament", exact: true }),
  ).toBeVisible();
}

async function omplirFormulari(page, dades) {
  await page.getByLabel("Municipi", { exact: true }).fill(dades.municipi);
  await page.getByLabel("Carrer i número", { exact: true }).fill(dades.carrer);
  await page.getByLabel("Pis, porta o escala", { exact: true }).fill(dades.pis);
  await page.getByLabel("Codi postal", { exact: true }).fill(dades.codi_postal);
}

test.describe("adreces de lliurament (US3)", () => {
  test("CP-US3-01 · afegeix una adreça nova", async ({ page }) => {
    await entrarComUsuari(page);

    await page.route(URL_ADRECES, async (ruta) => {
      if (ruta.request().method() === "GET") {
        await ruta.fulfill({ status: 200, contentType: "application/json", body: "[]" });
        return;
      }
      await ruta.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: 2,
          municipi: "Girona",
          carrer: "Carrer Nou 5",
          pis: "4t",
          codi_postal: "17001",
          predeterminada: false,
        }),
      });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Afegir nova adreça", exact: true }).click();
    await omplirFormulari(page, {
      municipi: "Girona",
      carrer: "Carrer Nou 5",
      pis: "4t",
      codi_postal: "17001",
    });
    await page.getByRole("button", { name: "Afegir adreça", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Carrer Nou 5", exact: true })).toBeVisible();
    await expect(page.getByText(/17001 Girona/)).toBeVisible();
  });

  test("CP-US3-02 · edita una adreça existent", async ({ page }) => {
    await entrarComUsuari(page);

    await page.route(URL_ADRECES, async (ruta) => {
      const peticio = ruta.request();
      if (peticio.method() === "GET") {
        await ruta.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([adreca()]) });
        return;
      }
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          municipi: "Girona",
          carrer: "Carrer Nou 5",
          pis: "4t",
          codi_postal: "17001",
          predeterminada: true,
        }),
      });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Editar l'adreça de Carrer Major 1", exact: true }).click();
    await omplirFormulari(page, {
      municipi: "Girona",
      carrer: "Carrer Nou 5",
      pis: "4t",
      codi_postal: "17001",
    });
    await page.getByRole("button", { name: "Desar canvis", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Carrer Nou 5", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Carrer Major 1", exact: true })).toHaveCount(0);
  });

  test("CP-US3-03 · suprimeix una adreça", async ({ page }) => {
    await entrarComUsuari(page);
    page.on("dialog", (dialog) => dialog.accept());

    await page.route(URL_ADRECES, async (ruta) => {
      if (ruta.request().method() === "GET") {
        await ruta.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([adreca()]) });
        return;
      }
      await ruta.fulfill({ status: 204, body: "" });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Suprimir l'adreça de Carrer Major 1", exact: true }).click();

    await expect(page.getByText("Encara no tens cap adreça desada.", { exact: true })).toBeVisible();
  });

  test("CP-US3-04 · marca una sola adreça com a predeterminada", async ({ page }) => {
    await entrarComUsuari(page);

    await page.route(URL_ADRECES, async (ruta) => {
      const peticio = ruta.request();
      if (peticio.method() === "GET") {
        await ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            adreca({ id: 1, predeterminada: true }),
            {
              id: 2,
              municipi: "Girona",
              carrer: "Carrer Nou 5",
              pis: "4t",
              codi_postal: "17001",
              predeterminada: false,
            },
          ]),
        });
        return;
      }
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(adreca({ id: 2, predeterminada: true })),
      });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Fer predeterminada l'adreça de Carrer Nou 5", exact: true }).click();

    await expect(page.getByRole("list", { name: "Adreces de lliurament" }).getByText("Predeterminada", { exact: true })).toHaveCount(1);
  });

  test("CP-US3-05 · mostra l'avís fora de la zona de servei", async ({ page }) => {
    await entrarComUsuari(page);

    await page.route(URL_ADRECES, async (ruta) => {
      if (ruta.request().method() === "GET") {
        await ruta.fulfill({ status: 200, contentType: "application/json", body: "[]" });
        return;
      }
      await ruta.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          codi_postal: ["Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida"],
        }),
      });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Afegir nova adreça", exact: true }).click();
    await omplirFormulari(page, {
      municipi: "Viladecans",
      carrer: "Carrer Fora 1",
      pis: "1r",
      codi_postal: "08840",
    });
    await page.getByRole("button", { name: "Afegir adreça", exact: true }).click();

    await expect(page.getByRole("alert").getByText(
      "Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida",
      { exact: true },
    )).toBeVisible();
  });

  test("valida els quatre camps obligatoris", async ({ page }) => {
    await entrarComUsuari(page);
    await page.route(URL_ADRECES, async (ruta) => {
      await ruta.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    });

    await obrirAdreces(page);
    await page.getByRole("button", { name: "Afegir nova adreça", exact: true }).click();
    await page.getByRole("button", { name: "Afegir adreça", exact: true }).click();

    await expect(page.getByText("Aquest camp és obligatori.", { exact: true })).toHaveCount(4);
  });
});
