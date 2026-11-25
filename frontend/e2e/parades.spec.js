import { test, expect } from "@playwright/test";

// Tests E2E de les parades de la ruta (US13-T8).
// L'API es simula amb page.route perquè els tests no depenen de dades reals.

const URL_RUTA = "**/api/prestecs/repartidor/ruta-avui/";
const URL_COMPLETAR = "**/api/prestecs/repartidor/parades/18/completar/";
const URL_FALLIDA = "**/api/prestecs/repartidor/parades/19/fallida/";

function parada(id, ordre, tipus, estatParada = "pendent", motiu = "") {
  return {
    id,
    ordre,
    tipus,
    comanda: 12,
    estat: tipus === "recollida" ? "preparada" : "en_cami",
    estat_parada: estatParada,
    motiu,
    llibres: [{ id: 7, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    adreca:
      tipus === "recollida"
        ? {
            biblioteca: { id: 3, nom: "Biblioteca Central" },
            text: null,
            latitud: null,
            longitud: null,
          }
        : {
            biblioteca: null,
            text: "C/ Major 1",
            latitud: null,
            longitud: null,
          },
  };
}

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

async function obrirRuta(page) {
  await page.goto("/repartidor/ruta");
  await expect(page.getByRole("heading", { name: "La meva ruta d'avui", exact: true })).toBeVisible();
}

test.describe("parades completades i fallides (US13)", () => {
  test("CP-US13-01 · completa una parada i mostra el nou estat", async ({ page }) => {
    await entrarComRepartidor(page);

    let estatParada = "pendent";
    await page.route(URL_RUTA, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          parada(18, 1, "recollida", estatParada),
          parada(19, 2, "lliurament"),
        ]),
      });
    });
    await page.route(URL_COMPLETAR, async (ruta) => {
      estatParada = "completada";
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 18, estat: "completada" }),
      });
    });

    await obrirRuta(page);
    await page
      .getByRole("button", { name: "Marcar la parada 1 com a completada", exact: true })
      .click();

    await expect(page.getByText("Parada 1 marcada com a completada.", { exact: true })).toBeVisible();
    await expect(page.locator(".estat-parada-completada")).toHaveText("Completada");
    await expect(
      page.getByRole("button", { name: "Marcar la parada 1 com a completada", exact: true }),
    ).toHaveCount(0);
  });

  test("CP-US13-02 · marca una parada com a fallida amb motiu", async ({ page }) => {
    await entrarComRepartidor(page);

    let estatParada = "pendent";
    let motiuActual = "";
    await page.route(URL_RUTA, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          parada(18, 1, "recollida"),
          parada(19, 2, "lliurament", estatParada, motiuActual),
        ]),
      });
    });
    await page.route(URL_FALLIDA, async (ruta) => {
      const cos = ruta.request().postDataJSON();
      motiuActual = cos.motiu;
      estatParada = "fallida";
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 19, estat: "fallida", motiu: motiuActual }),
      });
    });

    await obrirRuta(page);
    await page
      .getByRole("button", { name: "Marcar la parada 2 com a fallida", exact: true })
      .click();
    await page.getByLabel("Motiu de la parada fallida", { exact: true }).fill("No hi havia ningú.");
    await page.getByRole("button", { name: "Confirmar fallida", exact: true }).click();

    await expect(page.getByText("Parada 2 marcada com a fallida.", { exact: true })).toBeVisible();
    await expect(page.locator(".estat-parada-fallida")).toContainText("Fallida");
    await expect(page.locator(".estat-parada-fallida")).toContainText("No hi havia ningú.");
  });

  test("CP-US13-03 · no confirma una parada fallida sense motiu", async ({ page }) => {
    await entrarComRepartidor(page);
    await page.route(URL_RUTA, async (ruta) => {
      await ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          parada(18, 1, "recollida"),
          parada(19, 2, "lliurament"),
        ]),
      });
    });

    let peticionsFallida = 0;
    await page.route(URL_FALLIDA, async (ruta) => {
      peticionsFallida += 1;
      await ruta.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ motiu: ["Cal indicar el motiu."] }),
      });
    });

    await obrirRuta(page);
    await page
      .getByRole("button", { name: "Marcar la parada 2 com a fallida", exact: true })
      .click();
    await page.getByRole("button", { name: "Confirmar fallida", exact: true }).click();

    await expect(page.getByText("Cal indicar el motiu.", { exact: true })).toBeVisible();
    expect(peticionsFallida).toBe(0);
  });

  test("redirecciona un usuari sense el rol de repartidor", async ({ page }) => {
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

    await page.goto("/repartidor/ruta");

    await expect(page).toHaveURL("/");
  });
});
