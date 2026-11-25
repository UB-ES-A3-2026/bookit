import { test, expect } from "@playwright/test";

// Tests E2E de la ruta del repartidor (US12-T10).
// L'API i les tiles del mapa se simulen per mantenir els casos deterministes.

const URL_RUTA = "**/api/prestecs/repartidor/ruta-avui/";
const URL_TILES = "**/geoserveis.icgc.cat/**";
const TILE_TRANSPARENT = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jN8sAAAAASUVORK5CYII=",
  "base64",
);

function parada({
  id,
  ordre,
  tipus,
  comanda,
  biblioteca = null,
  adreca = null,
  latitud = null,
  longitud = null,
}) {
  return {
    id,
    ordre,
    tipus,
    comanda,
    estat: tipus === "recollida" ? "preparada" : "en_cami",
    llibres: [
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        portada: "",
      },
    ],
    adreca: { biblioteca, text: adreca, latitud, longitud },
  };
}

const PARADES = [
  parada({
    id: 18,
    ordre: 1,
    tipus: "recollida",
    comanda: 12,
    biblioteca: { id: 3, nom: "Biblioteca Central" },
    latitud: 41.385064,
    longitud: 2.173404,
  }),
  parada({
    id: 19,
    ordre: 2,
    tipus: "lliurament",
    comanda: 12,
    adreca: "C/ Major 1, Barcelona",
    latitud: 41.403629,
    longitud: 2.174355,
  }),
  parada({
    id: 20,
    ordre: 3,
    tipus: "recollida",
    comanda: 15,
    biblioteca: { id: 4, nom: "Biblioteca Gràcia" },
    latitud: 41.3981,
    longitud: 2.1568,
  }),
];

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

async function simularRuta(page, parades) {
  await page.route(URL_RUTA, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(parades),
    });
  });
  await page.route(URL_TILES, async (ruta) => {
    await ruta.fulfill({
      status: 200,
      contentType: "image/png",
      body: TILE_TRANSPARENT,
    });
  });
}

async function obrirRuta(page) {
  await page.goto("/repartidor/ruta");
  await expect(
    page.getByRole("heading", { name: "La meva ruta d'avui", exact: true }),
  ).toBeVisible();
}

test.describe("ruta del repartidor (US12)", () => {
  test("CP-US12-01 i CP-US12-03 · mostra les parades ordenades i recull abans de lliurar", async ({
    page,
  }) => {
    await entrarComRepartidor(page);
    await simularRuta(page, [...PARADES].reverse());

    await obrirRuta(page);

    const llista = page.getByRole("list", { name: "Parades de la ruta d'avui" });
    const paradesVisibles = llista.locator(".parada");
    await expect(paradesVisibles).toHaveCount(3);
    await expect(paradesVisibles.locator("h2")).toHaveText([
      "Parada 1: Recollida",
      "Parada 2: Lliurament",
      "Parada 3: Recollida",
    ]);
    await expect(paradesVisibles.locator(".lloc")).toHaveText([
      "Biblioteca Central",
      "C/ Major 1, Barcelona",
      "Biblioteca Gràcia",
    ]);

    const recollida = paradesVisibles.filter({ hasText: "Biblioteca Central" });
    const lliurament = paradesVisibles.filter({ hasText: "C/ Major 1, Barcelona" });
    await expect(recollida).toContainText("Comanda 12");
    await expect(lliurament).toContainText("Comanda 12");
    const posicioRecollida = await recollida.evaluate((element) =>
      Array.from(element.parentElement.children).indexOf(element),
    );
    const posicioLliurament = await lliurament.evaluate((element) =>
      Array.from(element.parentElement.children).indexOf(element),
    );
    expect(posicioRecollida).toBeLessThan(posicioLliurament);
  });

  test("CP-US12-02 · mostra al mapa totes les parades amb ubicació", async ({ page }) => {
    await entrarComRepartidor(page);
    await simularRuta(page, [...PARADES].reverse());

    await obrirRuta(page);

    await expect(
      page.getByRole("region", { name: "Mapa amb les parades de la ruta d'avui" }),
    ).toBeVisible();
    const marcadors = page.locator(".marcador-parada");
    await expect(marcadors).toHaveCount(3);
    await expect(marcadors.nth(0)).toHaveAttribute("title", "Parada 1: Recollida");
    await expect(marcadors.nth(1)).toHaveAttribute("title", "Parada 2: Lliurament");
    await expect(marcadors.nth(2)).toHaveAttribute("title", "Parada 3: Recollida");
  });

  test("manté a la llista les parades sense coordenades i avisa que no surten al mapa", async ({
    page,
  }) => {
    await entrarComRepartidor(page);
    const paradesAmbUbicacio = [
      PARADES[0],
      parada({
        id: 21,
        ordre: 2,
        tipus: "lliurament",
        comanda: 15,
        adreca: "Carrer sense coordenades",
      }),
    ];
    await simularRuta(page, paradesAmbUbicacio);

    await obrirRuta(page);

    const llista = page.getByRole("list", { name: "Parades de la ruta d'avui" });
    await expect(llista.locator(".parada")).toHaveCount(2);
    await expect(llista.getByText("Carrer sense coordenades", { exact: true })).toBeVisible();
    await expect(page.locator(".marcador-parada")).toHaveCount(1);
    await expect(
      page.getByText("1 parada no surt al mapa perquè no en tenim la ubicació. La tens a la llista.", {
        exact: true,
      }),
    ).toBeVisible();
  });

  test("redirigeix a l'inici un usuari que no té el rol de repartidor", async ({ page }) => {
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
