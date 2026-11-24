import { test, expect } from "@playwright/test";

// Tests E2E de l'estat i les notificacions de les comandes (US8-T9).
// Els endpoints es simulen amb page.route perquè no hi ha una fixture E2E
// que provoqui els quatre canvis d'estat i les seves notificacions.

const URL_COMANDES = "**/api/prestecs/comandes/";
const URL_NOTIFICACIONS = "**/api/prestecs/notificacions/";

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

function comanda(id, estat, data = "2026-11-24") {
  return {
    id,
    estat,
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 7, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "" }],
    data_lliurament: estat === "cancellada" ? null : data,
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

test.describe("estat i notificacions de la comanda (US8)", () => {
  test("CP-US8-01 i CP-US8-02 · mostra els estats rebuda i preparada", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [
      comanda(12, "rebuda"),
      comanda(11, "preparada", "2026-11-25"),
    ]);

    await obrirComandes(page);

    await expect(targeta(page, 12).getByText("Rebuda", { exact: true })).toBeVisible();
    await expect(targeta(page, 11).getByText("Preparada", { exact: true })).toBeVisible();
  });

  test("CP-US8-03 i CP-US8-04 · mostra en camí i lliurada", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [
      comanda(12, "en_cami", "2026-11-25"),
      comanda(11, "lliurada", "2026-11-20"),
    ]);

    await obrirComandes(page);

    await expect(targeta(page, 12).getByText("En camí", { exact: true })).toBeVisible();
    await expect(targeta(page, 11).getByText("Lliurada", { exact: true })).toBeVisible();
    await expect(targeta(page, 11).getByText("Data de lliurament", { exact: true })).toBeVisible();
  });

  test("CP-US8-02 · mostra la notificació de comanda preparada", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "preparada")]);

    await page.route(URL_NOTIFICACIONS, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{
          id: 31,
          comanda: 12,
          text: "La teva comanda ja està preparada i aviat sortirà cap a casa teva",
          llegida: false,
          creada: "2026-11-17T09:05:00Z",
        }]),
      });
    });

    await obrirComandes(page);

    await page.getByRole("button", { name: /Notificacions/ }).click();
    await expect(page.getByRole("region", { name: "Llista de notificacions" }).getByText(
      "La teva comanda ja està preparada i aviat sortirà cap a casa teva",
      { exact: true },
    )).toBeVisible();
  });

  test("CP-US8-01 i CP-US8-06 · mostra la notificació rebuda i marca-la llegida", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, [comanda(12, "rebuda")]);

    await page.route(URL_NOTIFICACIONS, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{
          id: 30,
          comanda: 12,
          text: "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant",
          llegida: false,
          creada: "2026-11-16T16:20:00Z",
        }]),
      });
    });

    await page.route("**/api/prestecs/notificacions/*/llegida/", async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 30,
          comanda: 12,
          text: "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant",
          llegida: true,
          creada: "2026-11-16T16:20:00Z",
        }),
      });
    });

    await obrirComandes(page);

    await page.getByRole("button", { name: /Notificacions/ }).click();
    await page.getByRole("button", { name: "Marcar com a llegida", exact: true }).click();

    await expect(page.getByRole("button", { name: "Marcar com a llegida", exact: true })).toHaveCount(0);
  });

  test("mostra el missatge quan no hi ha comandes", async ({ page }) => {
    await entrarComUsuari(page);
    await simularComandes(page, []);

    await obrirComandes(page);

    await expect(page.getByText("Encara no has fet cap comanda.", { exact: true })).toBeVisible();
  });

  test("redirigeix un usuari sense rol", async ({ page }) => {
    await page.addInitScript(() => {
      sessionStorage.setItem("bookit.sessio", JSON.stringify({
        accessToken: "token-e2e-repartidor",
        refreshToken: null,
        usuari: { id: 2, nom: "Repartidor E2E", rol: "repartidor" },
        rol: "repartidor",
      }));
    });

    await page.goto("/comandes");

    await expect(page).toHaveURL("/");
  });
});
