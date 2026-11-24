import { test, expect } from "@playwright/test";

// Tests E2E de les comandes pendents de la biblioteca (US10-T6).
// La resposta de l'endpoint es simula perquè no hi ha fixtures E2E dedicades.

const URL_COMANDES = "**/api/prestecs/biblioteca/comandes/";

async function entrarComBiblioteca(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-biblioteca",
        refreshToken: "refresh-e2e-biblioteca",
        usuari: { id: 3, nom: "Biblioteca Montbau", rol: "biblioteca" },
        rol: "biblioteca",
      }),
    );
  });
}

function comanda({ id, estat = "rebuda", data = "2026-11-20", usuari = "Anna Puig", titol = "Solitud" }) {
  return {
    id,
    estat,
    usuari: { id: 25, nom: usuari },
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 9, titol, autor: "Víctor Català", portada: "" }],
    data_lliurament: data,
    creada: "2026-11-16T16:20:00Z",
  };
}

async function simularComandes(page, comandes) {
  await page.route(URL_COMANDES, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comandes),
    });
  });
}

async function obrirComandes(page) {
  await page.goto("/biblioteca/comandes");
  await expect(page.getByRole("heading", { name: "Comandes pendents", exact: true })).toBeVisible();
}

function llista(page) {
  return page.getByRole("list", { name: "Comandes pendents" });
}

function targeta(page, id) {
  return llista(page)
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: `Comanda ${id}`, exact: true }) });
}

test.describe("comandes pendents de la biblioteca (US10)", () => {
  test("CP-US10-01 i CP-US10-05 · conserva l'ordre i mostra les dades", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, [
      comanda({ id: 12, estat: "rebuda", data: "2026-11-20", usuari: "Anna Puig", titol: "Solitud" }),
      comanda({ id: 4, estat: "preparada", data: "2026-11-28", usuari: "Jordi Soler", titol: "La plaça del Diamant" }),
      comanda({ id: 8, estat: "cancellada", data: null, usuari: "Marta Puig", titol: "Incerta" }),
    ]);

    await obrirComandes(page);

    await expect(llista(page).getByRole("heading", { level: 2 })).toHaveText([
      "Comanda 12",
      "Comanda 4",
      "Comanda 8",
    ]);

    await expect(targeta(page, 12).getByText("Solitud", { exact: true })).toBeVisible();
    await expect(targeta(page, 12).getByText("Anna Puig", { exact: true })).toBeVisible();
    await expect(targeta(page, 12).getByText("20/11/2026", { exact: true })).toBeVisible();
    await expect(targeta(page, 8).getByText("Sense data", { exact: true })).toBeVisible();
  });

  test("CP-US10-02 · mostra els estats rebuda, preparada i cancel·lada", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, [
      comanda({ id: 12, estat: "rebuda", data: "2026-11-20" }),
      comanda({ id: 4, estat: "preparada", data: "2026-11-28" }),
      comanda({ id: 8, estat: "cancellada", data: null }),
    ]);

    await obrirComandes(page);

    await expect(targeta(page, 12).getByText("Rebuda", { exact: true })).toBeVisible();
    await expect(targeta(page, 4).getByText("Preparada", { exact: true })).toBeVisible();
    await expect(targeta(page, 8).getByText("Cancel·lada", { exact: true })).toBeVisible();
    await expect(targeta(page, 8).getByText("L'usuari l'ha cancel·lada: no cal preparar-la.", { exact: true })).toBeVisible();
  });

  test("CP-US10-04 · mostra el missatge quan no hi ha comandes", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, []);

    await obrirComandes(page);

    await expect(page.getByText("No tens cap comanda pendent.", { exact: true })).toBeVisible();
    await expect(page.getByRole("list", { name: "Comandes pendents" })).toHaveCount(0);
  });

  test("mostrar dades de les comandes sense data al final", async ({ page }) => {
    await entrarComBiblioteca(page);
    await simularComandes(page, [
      comanda({ id: 12, estat: "rebuda", data: "2026-11-20" }),
      comanda({ id: 8, estat: "cancellada", data: null }),
    ]);

    await obrirComandes(page);

    await expect(llista(page).getByRole("heading", { level: 2 })).toHaveText([
      "Comanda 12",
      "Comanda 8",
    ]);
    await expect(targeta(page, 8).getByText("Demanada el", { exact: true })).toBeVisible();
  });

  test("redirigeix un usuari sense rol de biblioteca", async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("bookit.sessio", JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: null,
        usuari: { id: 25, nom: "Usuari E2E", rol: "usuari" },
        rol: "usuari",
      }));
    });

    await page.goto("/biblioteca/comandes");

    await expect(page).toHaveURL("/");
  });
});
