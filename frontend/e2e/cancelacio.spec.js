import { test, expect } from "@playwright/test";

// Tests E2E de la cancel·lació d'una comanda (US20-T6).
// La llista i el POST es simulen perquè no hi ha una fixture E2E dedicada.

const URL_COMANDES = "**/api/prestecs/comandes/";

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

function comanda(id, estat) {
  return {
    id,
    estat,
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 7, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "" }],
    data_lliurament: estat === "lliurada" ? "2026-11-20" : "2026-11-25",
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
  await page.goto("/comandes");
  await expect(page.getByRole("heading", { name: "Les meves comandes", exact: true })).toBeVisible();
}

function targeta(page, id) {
  return page
    .getByRole("list", { name: "Les meves comandes" })
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: `Comanda ${id}`, exact: true }) });
}

test.describe("cancel·lació d'una comanda (US20)", () => {
  test("CP-US20-01 i CP-US20-03 · demana confirmació i cancel·la", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "rebuda")]);

    let confirmacio;
    page.on("dialog", async (dialog) => {
      confirmacio = dialog.message();
      await dialog.accept();
    });

    await page.route("**/api/prestecs/comandes/*/cancellar/", async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(comanda(12, "cancellada")),
      });
    });

    await obrirComandes(page);
    await targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true }).click();

    expect(confirmacio).toBe("Segur que vols cancel·lar aquesta comanda?");
    await expect(targeta(page, 12).getByText("Cancel·lada", { exact: true })).toBeVisible();
    await expect(targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true })).toHaveCount(0);
  });

  test("CP-US20-02 · rebutja la confirmació i no envia cap cancel·lació", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "preparada")]);

    let peticioCancelacio = false;
    await page.route("**/api/prestecs/comandes/*/cancellar/", async (ruta) => {
      peticioCancelacio = true;
      await ruta.abort();
    });

    page.on("dialog", (dialog) => dialog.dismiss());

    await obrirComandes(page);
    await targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true }).click();

    expect(peticioCancelacio).toBe(false);
    await expect(targeta(page, 12).getByText("Preparada", { exact: true })).toBeVisible();
  });

  test("CP-US20-03 · mostra una comanda cancel·lada sense acció", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "cancellada")]);

    await obrirComandes(page);

    await expect(targeta(page, 12).getByText("Cancel·lada", { exact: true })).toBeVisible();
    await expect(targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true })).toHaveCount(0);
  });

  test("CP-US20-07 · no cancel·la una comanda en camí", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "en_cami")]);

    let peticioCancelacio = false;
    await page.route("**/api/prestecs/comandes/*/cancellar/", async (ruta) => {
      peticioCancelacio = true;
      await ruta.abort();
    });

    await obrirComandes(page);
    await targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true }).click();

    expect(peticioCancelacio).toBe(false);
    await expect(targeta(page, 12).getByText("Aquesta comanda ja ha sortit i no es pot cancel·lar", { exact: true })).toBeVisible();
  });

  test("CP-US20-07 · no cancel·la una comanda lliurada", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "lliurada")]);

    await obrirComandes(page);
    await targeta(page, 12).getByRole("button", { name: "Cancel·lar comanda", exact: true }).click();

    await expect(targeta(page, 12).getByText("Aquesta comanda ja ha sortit i no es pot cancel·lar", { exact: true })).toBeVisible();
  });
});
