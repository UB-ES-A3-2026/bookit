import { test, expect } from "@playwright/test";

// Tests E2E dels llibres en préstec (US19-T7).
// L'API es simula amb page.route perquè el projecte no té una fixture E2E
// que creï préstecs i els dades amb dates controlades.

const URL_PRESTECS = "**/api/prestecs/prestecs/";

async function entrarComUsuari(page) {
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "bookit.sessio",
      JSON.stringify({
        accessToken: "token-e2e-usuari",
        refreshToken: "refresh-e2e-usuari",
        usuari: { id: 1, nom: "Usuari E2E", rol: "usuari" },
        rol: "usuari",
      }),
    );
  });
}

async function obrirPrestecs(page) {
  await page.goto("/prestecs");
  await expect(
    page.getByRole("heading", { name: "Els meus préstecs", exact: true }),
  ).toBeVisible();
}

function prestec({ id, titol, autor, biblioteca, inici, limit, superat, portada = "" }) {
  return {
    id,
    llibre: {
      id: id + 100,
      titol,
      autor,
      portada,
    },
    biblioteca: {
      id: id,
      nom: biblioteca,
    },
    data_inici: inici,
    data_limit: limit,
    termini_superat: superat,
  };
}

async function simularPrestecs(page, prestecs) {
  await page.route(URL_PRESTECS, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(prestecs),
    });
  });
}

function llistaPrestecs(page) {
  return page.getByRole("list", { name: "Llibres en préstec" });
}

test.describe("els meus préstecs (US19)", () => {
  test("CP-US19-01 i CP-US19-02 · mostra la llista i les dades del préstec", async ({ page }) => {
    await entrarComUsuari(page);
    await simularPrestecs(page, [
      prestec({
        id: 21,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        biblioteca: "Biblioteca Montbau",
        inici: "2026-10-10",
        limit: "2026-11-09",
        superat: true,
      }),
      prestec({
        id: 22,
        titol: "Solitud",
        autor: "Víctor Català",
        biblioteca: "Biblioteca Gràcia",
        inici: "2026-11-18",
        limit: "2026-12-18",
        superat: false,
      }),
    ]);

    await obrirPrestecs(page);

    const llista = llistaPrestecs(page);
    await expect(llista.getByRole("listitem")).toHaveCount(2);

    const primer = llista.getByRole("listitem").first();
    await expect(primer.getByRole("heading", { name: "La plaça del Diamant", exact: true })).toBeVisible();
    await expect(primer.getByText("Mercè Rodoreda", { exact: true })).toBeVisible();
    await expect(primer.getByText("Biblioteca Montbau", { exact: true })).toBeVisible();
    await expect(primer.getByText("10/10/2026", { exact: true })).toBeVisible();
    await expect(primer.getByText("09/11/2026", { exact: true })).toBeVisible();

    const segon = llista.getByRole("listitem").nth(1);
    await expect(segon.getByRole("heading", { name: "Solitud", exact: true })).toBeVisible();
    await expect(segon.getByText("Biblioteca Gràcia", { exact: true })).toBeVisible();
  });

  test("CP-US19-03 · conserva l'ordre rebut per la API", async ({ page }) => {
    await entrarComUsuari(page);
    await simularPrestecs(page, [
      prestec({ id: 1, titol: "Préstec proper", autor: "Autor A", biblioteca: "Biblioteca A", inici: "2026-10-01", limit: "2026-11-09", superat: true }),
      prestec({ id: 2, titol: "Préstec futur", autor: "Autor B", biblioteca: "Biblioteca B", inici: "2026-10-15", limit: "2026-12-18", superat: false }),
    ]);

    await obrirPrestecs(page);

    const titols = llistaPrestecs(page).getByRole("heading", { level: 2 });
    await expect(titols).toHaveText(["Préstec proper", "Préstec futur"]);
  });

  test("CP-US19-04 · destaca només els préstecs vençuts", async ({ page }) => {
    await entrarComUsuari(page);
    await simularPrestecs(page, [
      prestec({ id: 1, titol: "Llibre vençut", autor: "Autor A", biblioteca: "Biblioteca A", inici: "2026-10-01", limit: "2026-11-09", superat: true }),
      prestec({ id: 2, titol: "Llibre d'avui", autor: "Autor B", biblioteca: "Biblioteca B", inici: "2026-10-20", limit: "2026-11-24", superat: false }),
      prestec({ id: 3, titol: "Llibre futur", autor: "Autor C", biblioteca: "Biblioteca C", inici: "2026-11-01", limit: "2026-12-18", superat: false }),
    ]);

    await obrirPrestecs(page);

    const llista = llistaPrestecs(page);
    const vençut = llista.getByRole("listitem").filter({ hasText: "Llibre vençut" });
    await expect(vençut.getByText("Termini de devolució superat", { exact: true })).toBeVisible();

    const avui = llista.getByRole("listitem").filter({ hasText: "Llibre d'avui" });
    await expect(avui.getByText("Termini de devolució superat", { exact: true })).toHaveCount(0);

    const futur = llista.getByRole("listitem").filter({ hasText: "Llibre futur" });
    await expect(futur.getByText("Termini de devolució superat", { exact: true })).toHaveCount(0);
  });

  test("CP-US19-06 · mostra el missatge quan no hi ha préstecs", async ({ page }) => {
    await entrarComUsuari(page);
    await simularPrestecs(page, []);

    await obrirPrestecs(page);

    await expect(page.getByText("No tens cap llibre en préstec", { exact: true })).toBeVisible();
    await expect(page.getByRole("list", { name: "Llibres en préstec" })).toHaveCount(0);
  });

  test("CP-US19-05 · mostra el control de devolució desactivat", async ({ page }) => {
    await entrarComUsuari(page);
    await simularPrestecs(page, [
      prestec({ id: 1, titol: "Solitud", autor: "Víctor Català", biblioteca: "Biblioteca Gràcia", inici: "2026-11-18", limit: "2026-12-18", superat: false }),
    ]);

    await obrirPrestecs(page);

    await expect(
      page.getByRole("button", { name: "Programar la devolució", exact: true }),
    ).toBeDisabled();
  });

  test("rediregeix un usuari sense rol a l'inici", async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem(
        "bookit.sessio",
        JSON.stringify({
          accessToken: "token-e2e-repartidor",
          refreshToken: null,
          usuari: { id: 2, nom: "Repartidor E2E", rol: "repartidor" },
          rol: "repartidor",
        }),
      );
    });

    await page.goto("/prestecs");

    await expect(page).toHaveURL("/");
  });

  test("mostra l'error si la càrrega falla", async ({ page }) => {
    await entrarComUsuari(page);
    await page.route(URL_PRESTECS, async (ruta) => {
      await ruta.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Error intern." }),
      });
    });

    await obrirPrestecs(page);

    await expect(
      page.getByText("No s'han pogut carregar els llibres en préstec.", { exact: true }),
    ).toBeVisible();
  });
});
