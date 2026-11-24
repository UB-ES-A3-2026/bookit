import { test, expect } from "@playwright/test";

// Tests E2E de les franges de disponibilitat (US14-T8).
// L'API es simula amb page.route perquè Playwright no té fixture pròpia
// per validar i iniciar sessió amb un repartidor.

const URL_FRANGES = "**/api/usuaris/repartidor/franges/";

async function entrarComRepartidor(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-repartidor",
        refreshToken: "refresh-e2e-repartidor",
        usuari: { id: 1, nom: "Repartidor E2E", rol: "repartidor" },
        rol: "repartidor",
      }),
    );
  });
}

async function simularFranges(page, inicials) {
  await page.route(URL_FRANGES, async (ruta) => {
    const peticio = ruta.request();

    if (peticio.method() === "GET") {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ franges: inicials }),
      });
      return;
    }

    if (peticio.method() === "PUT") {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          franges: peticio.postDataJSON().franges.map((franja, index) => ({
            id: index + 1,
            ...franja,
          })),
        }),
      });
    }
  });
}

async function afegirFranja(page, dia, inici, fi) {
  await page
    .getByRole("button", { name: `Afegir una franja el ${dia.toLowerCase()}`, exact: true })
    .click();

  await page
    .getByLabel(`Hora d'inici, ${dia.toLowerCase()}`, { exact: true })
    .last()
    .fill(inici);
  await page
    .getByLabel(`Hora de final, ${dia.toLowerCase()}`, { exact: true })
    .last()
    .fill(fi);
}

async function obrirPagina(page) {
  await page.goto("/repartidor/franges");
  await expect(
    page.getByRole("heading", { name: "Franges de disponibilitat", exact: true }),
  ).toBeVisible();
}

test.describe("franges de disponibilitat (US14)", () => {
  test("CP-US14-02 · desa i mostra franges setmanals vàlides", async ({ page }) => {
    await entrarComRepartidor(page);
    await simularFranges(page, []);

    await obrirPagina(page);

    await afegirFranja(page, "Dilluns", "09:00", "13:00");
    await afegirFranja(page, "Divendres", "09:00", "14:30");

    await page
      .getByRole("button", { name: "Desar les franges", exact: true })
      .click();

    await expect(page.getByText("S'han desat les teves franges.", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Hora d'inici, dilluns", { exact: true })).toHaveValue("09:00");
    await expect(page.getByLabel("Hora de final, dilluns", { exact: true })).toHaveValue("13:00");
    await expect(page.getByLabel("Hora d'inici, divendres", { exact: true })).toHaveValue("09:00");
    await expect(page.getByLabel("Hora de final, divendres", { exact: true })).toHaveValue("14:30");
  });

  test("CP-US14-03 · substitueix l'horari i permet buidar-lo", async ({ page }) => {
    await entrarComRepartidor(page);
    await simularFranges(page, [
      { id: 4, dia: 0, hora_inici: "09:00", hora_fi: "13:00" },
      { id: 5, dia: 4, hora_inici: "09:00", hora_fi: "14:30" },
    ]);

    await obrirPagina(page);

    await page
      .getByRole("button", { name: "Treure la franja del dilluns", exact: true })
      .click();

    await page
      .getByRole("button", { name: "Treure la franja del divendres", exact: true })
      .click();

    await expect(page.getByText("No disponible", { exact: true })).toHaveCount(7);

    await page
      .getByRole("button", { name: "Desar les franges", exact: true })
      .click();

    await expect(page.getByText("S'han desat les teves franges.", { exact: true })).toBeVisible();
  });

  test("CP-US14-04 · mostra l'error de franges solapades", async ({ page }) => {
    await entrarComRepartidor(page);

    await page.route(URL_FRANGES, async (ruta) => {
      const peticio = ruta.request();

      if (peticio.method() === "GET") {
        await ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ franges: [] }),
        });
        return;
      }

      await ruta.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          franges: [
            "Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen.",
          ],
        }),
      });
    });

    await obrirPagina(page);

    await afegirFranja(page, "Dilluns", "09:00", "13:00");
    await afegirFranja(page, "Dilluns", "12:00", "14:00");

    await page
      .getByRole("button", { name: "Desar les franges", exact: true })
      .click();

    await expect(
      page.getByText(
        "Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen.",
        { exact: true },
      ),
    ).toBeVisible();
  });

  test("CP-US14-10 · redirigeix un usuari sense rol de repartidor", async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem(
        "bookit.sessio",
        JSON.stringify({
          accessToken: "token-e2e-usuari",
          refreshToken: null,
          usuari: { id: 2, nom: "Usuari E2E", rol: "usuari" },
          rol: "usuari",
        }),
      );
    });

    await page.goto("/repartidor/franges");

    await expect(page).toHaveURL("/");
  });
});
