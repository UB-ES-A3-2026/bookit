import { test, expect } from "@playwright/test";

// Tests E2E de marcar una comanda com a llesta (US15-T6).
// La llista i el POST es simulen amb page.route perquè no hi ha una fixture
// E2E que creï comandes de prova i les relacione amb una biblioteca verificada.

const URL_COMANDES = "**/api/prestecs/biblioteca/comandes/**";

async function entrarComBiblioteca(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-biblioteca",
        refreshToken: "refresh-e2e-biblioteca",
        usuari: { id: 3, nom: "Biblioteca E2E", rol: "biblioteca" },
        rol: "biblioteca",
      }),
    );
  });
}

function comanda({ id, estat = "rebuda", data = "2026-11-20" }) {
  return {
    id,
    estat,
    usuari: { id: 25, nom: "Anna Puig" },
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 7, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "" }],
    data_lliurament: data,
    creada: "2026-11-16T16:20:00Z",
  };
}

async function obrirComandes(page) {
  await page.goto("/biblioteca/comandes");
  await expect(
    page.getByRole("heading", { name: "Comandes pendents", exact: true }),
  ).toBeVisible();
}

async function simularComandes(page, comandes) {
  await page.route(URL_COMANDES, async (ruta) => {
    if (ruta.request().method() === "GET") {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(comandes),
      });
      return;
    }

    await ruta.fallback();
  });
}

function targeta(page, id) {
  return page
    .getByRole("list", { name: "Comandes pendents" })
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: `Comanda ${id}`, exact: true }) });
}

test.describe("comanda llesta per a recollida (US15)", () => {
  test("CP-US15-01 · mostra l'acció per a una comanda rebuda", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, [comanda({ id: 12 })]);

    await obrirComandes(page);

    const targetaComanda = targeta(page, 12);
    await expect(targetaComanda.getByText("Rebuda", { exact: true })).toBeVisible();
    await expect(
      targetaComanda.getByRole("button", { name: "Llesta per a recollida", exact: true }),
    ).toBeVisible();
  });

  test("CP-US15-02 · marca la comanda i actualitza l'estat sense recarregar", async ({ page }) => {
    await entrarComBiblioteca(page);

    await page.route(URL_COMANDES, async (ruta) => {
      const peticio = ruta.request();
      if (peticio.method() === "GET") {
        await ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([comanda({ id: 12 })]),
        });
        return;
      }

      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(comanda({ id: 12, estat: "preparada" })),
      });
    });

    await obrirComandes(page);

    await targeta(page, 12)
      .getByRole("button", { name: "Llesta per a recollida", exact: true })
      .click();

    const targetaComanda = targeta(page, 12);
    await expect(targetaComanda.getByText("Preparada", { exact: true })).toBeVisible();
    await expect(
      targetaComanda.getByRole("button", { name: "Llesta per a recollida", exact: true }),
    ).toHaveCount(0);
  });

  test("CP-US15-05 · mostra l'error si la comanda ja està preparada", async ({ page }) => {
    await entrarComBiblioteca(page);

    await page.route(URL_COMANDES, async (ruta) => {
      const peticio = ruta.request();
      if (peticio.method() === "GET") {
        await ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([comanda({ id: 12 })]),
        });
        return;
      }

      await ruta.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Aquesta comanda ja està llesta per a recollida." }),
      });
    });

    await obrirComandes(page);

    await targeta(page, 12)
      .getByRole("button", { name: "Llesta per a recollida", exact: true })
      .click();

    await expect(
      targeta(page, 12).getByRole("alert").getByText(
        "Aquesta comanda ja està llesta per a recollida.",
        { exact: true },
      ),
    ).toBeVisible();
  });

  test("CP-US15-01 · no mostra l'acció per a una comanda preparada", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, [comanda({ id: 12, estat: "preparada" })]);

    await obrirComandes(page);

    const targetaComanda = targeta(page, 12);
    await expect(targetaComanda.getByText("Preparada", { exact: true })).toBeVisible();
    await expect(
      targetaComanda.getByRole("button", { name: "Llesta per a recollida", exact: true }),
    ).toHaveCount(0);
  });

  test("rediregeix un usuari sense rol de biblioteca", async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem(
        "bookit.sessio",
        JSON.stringify({
          accessToken: "token-e2e-usuari",
          refreshToken: null,
          usuari: { id: 25, nom: "Usuari E2E", rol: "usuari" },
          rol: "usuari",
        }),
      );
    });

    await page.goto("/biblioteca/comandes");

    await expect(page).toHaveURL("/");
  });
});
