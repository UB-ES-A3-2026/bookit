import { test, expect } from "@playwright/test";

// Tests E2E del cercador de la pàgina d'inici (US4-T7).
// La pàgina de resultats amb les dades de l'API és la US4-T8; aquí només es comprova que el cercador hi porta.

const campCerca = (page) => page.getByRole("searchbox", { name: "Cerca llibres per títol, autor o ISBN" });
const botoCercar = (page) => page.getByRole("button", { name: "Buscar llibres" });

test("el cercador es veu a la pàgina d'inici", async ({ page }) => {
  await page.goto("/");

  await expect(campCerca(page)).toBeVisible();
  await expect(campCerca(page)).toHaveAttribute("placeholder", "Quin llibre busques?");
  await expect(botoCercar(page)).toBeVisible();
});

test("cercar amb el botó porta als resultats amb el text cercat", async ({ page }) => {
  await page.goto("/");

  await campCerca(page).fill("  La plaça del Diamant  ");
  await botoCercar(page).click();

  await expect(page).toHaveURL("/cerca?q=La+pla%C3%A7a+del+Diamant");
  await expect(page.getByRole("heading", { name: "Resultats de la cerca" })).toBeVisible();
  await expect(page.getByText("Has cercat «La plaça del Diamant».")).toBeVisible();
});

test("cercar amb la tecla Enter també porta als resultats", async ({ page }) => {
  await page.goto("/");

  await campCerca(page).fill("Mercè Rodoreda");
  await campCerca(page).press("Enter");

  await expect(page).toHaveURL("/cerca?q=Merc%C3%A8+Rodoreda");
});

for (const text of ["", "   "]) {
  test(`amb el camp ${text ? "amb només espais" : "buit"} no es cerca res`, async ({ page }) => {
    await page.goto("/");

    await campCerca(page).fill(text);
    await botoCercar(page).click();

    await expect(page).toHaveURL("/");
    await expect(campCerca(page)).toBeFocused();
  });
}

test.describe("en mòbil", () => {
  test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

  test("el cercador cap a la pantalla sense desplaçament horitzontal", async ({ page }) => {
    await page.goto("/");

    await expect(botoCercar(page)).toBeInViewport({ ratio: 1 });
    const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(ampladaPagina).toBeLessThanOrEqual(375);
  });
});

// Tests E2E de la pàgina de resultats (US4-T8). L'API es simula amb page.route perquè encara no hi ha dades
// d'exemple del catàleg (US4-T4).
test.describe("pàgina de resultats (US4-T8)", () => {
  const CAPCALERES_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
  };

  const llibres = [
    {
      id: 1,
      titol: "La plaça del Diamant",
      autor: "Mercè Rodoreda",
      isbn: "9788475882574",
      portada: "https://example.com/portades/placa.jpg",
      disponible: true,
      mitjana_valoracions: 4.25,
      nombre_valoracions: 12,
    },
    {
      id: 2,
      titol: "Mirall trencat",
      autor: "Mercè Rodoreda",
      isbn: "9788475881355",
      portada: "",
      disponible: false,
      mitjana_valoracions: null,
      nombre_valoracions: 0,
    },
  ];

  const resposta = (results, canvis = {}) => ({
    count: results.length,
    next: null,
    previous: null,
    results,
    ...canvis,
  });

  // Respon les peticions de cerca i en desa els paràmetres per poder-los comprovar.
  async function simulaCerca(page, estat, cos) {
    const peticions = [];
    await page.route("**/api/cataleg/llibres/**", async (route) => {
      if (route.request().method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: CAPCALERES_CORS });
        return;
      }
      peticions.push(new URL(route.request().url()).searchParams);
      await route.fulfill({ status: estat, headers: CAPCALERES_CORS, json: cos });
    });
    return peticions;
  }

  const targetes = (page) => page.getByRole("list", { name: "Resultats de la cerca" }).getByRole("listitem");

  test("demana a l'API el text cercat", async ({ page }) => {
    const peticions = await simulaCerca(page, 200, resposta(llibres));
    await page.goto("/cerca?q=Rodoreda");

    await expect(targetes(page)).toHaveCount(2);
    expect(peticions[0].get("q")).toBe("Rodoreda");
    expect(peticions[0].get("page")).toBe("1");
  });

  test("mostra el títol, l'autor, la disponibilitat i les valoracions de cada llibre", async ({ page }) => {
    await simulaCerca(page, 200, resposta(llibres));
    await page.goto("/cerca?q=Rodoreda");

    await expect(page.getByText("2 resultats.")).toBeVisible();
    const primer = targetes(page).nth(0);
    await expect(primer.getByRole("heading", { name: "La plaça del Diamant" })).toBeVisible();
    await expect(primer).toContainText("Mercè Rodoreda");
    await expect(primer).toContainText("Disponible");
    await expect(primer).toContainText("4,3 de 5 · 12 valoracions");

    const segon = targetes(page).nth(1);
    await expect(segon).toContainText("No disponible");
    await expect(segon).toContainText("Sense valoracions");
  });

  test("mostra la portada o, si no n'hi ha, una imatge per defecte", async ({ page }) => {
    await simulaCerca(page, 200, resposta(llibres));
    await page.goto("/cerca?q=Rodoreda");

    await expect(targetes(page).nth(0).getByRole("img", { name: "Portada de La plaça del Diamant" })).toHaveAttribute(
      "src",
      llibres[0].portada,
    );
    await expect(targetes(page).nth(1).getByRole("img")).toHaveCount(0);
    await expect(targetes(page).nth(1).locator(".portada-per-defecte")).toBeVisible();
  });

  test("mostra un missatge mentre cerca", async ({ page }) => {
    await page.route("**/api/cataleg/llibres/**", () => {});
    await page.goto("/cerca?q=Rodoreda");

    await expect(page.getByRole("status")).toHaveText("Cercant llibres...");
  });

  test("mostra un error si l'API falla i permet tornar-ho a provar", async ({ page }) => {
    let intents = 0;
    await page.route("**/api/cataleg/llibres/**", async (route) => {
      intents += 1;
      if (intents === 1) {
        await route.fulfill({ status: 500, headers: CAPCALERES_CORS, body: "" });
        return;
      }
      await route.fulfill({ status: 200, headers: CAPCALERES_CORS, json: resposta(llibres) });
    });
    await page.goto("/cerca?q=Rodoreda");

    await expect(page.getByRole("alert")).toContainText("No s'ha pogut fer la cerca.");
    await page.getByRole("button", { name: "Tornar-ho a provar" }).click();

    await expect(page.getByRole("alert")).toHaveCount(0);
    await expect(targetes(page)).toHaveCount(2);
  });

  test("mostra un error si el servidor no respon", async ({ page }) => {
    await page.route("**/api/cataleg/llibres/**", (route) => route.abort());
    await page.goto("/cerca?q=Rodoreda");

    await expect(page.getByRole("alert")).toContainText("No s'ha pogut fer la cerca.");
  });

  test("passa a la pàgina següent de resultats", async ({ page }) => {
    const peticions = await simulaCerca(page, 200, resposta(llibres, { count: 12, next: "pagina-2" }));
    await page.goto("/cerca?q=Rodoreda");

    await expect(page.getByRole("button", { name: "Anterior" })).toBeDisabled();
    await page.getByRole("button", { name: "Següent" }).click();

    await expect(page).toHaveURL("/cerca?q=Rodoreda&pagina=2");
    await expect.poll(() => peticions.at(-1)?.get("page")).toBe("2");
  });

  test("sense text cercat no es fa cap petició", async ({ page }) => {
    const peticions = await simulaCerca(page, 200, resposta(llibres));
    await page.goto("/cerca");

    await expect(page.getByText("Escriu el títol, l'autor o l'ISBN al cercador de la pàgina d'inici.")).toBeVisible();
    expect(peticions).toHaveLength(0);
  });

  test.describe("sense resultats (US4-T9)", () => {
    const MISSATGE = "No s'ha trobat el llibre cercat, assegura't que l'informació introduïda sigui correcta";

    test("mostra el missatge quan la cerca no troba cap llibre", async ({ page }) => {
      await simulaCerca(page, 200, resposta([]));
      await page.goto("/cerca?q=llibre que no existeix");

      await expect(page.getByText(MISSATGE)).toBeVisible();
      await expect(page.getByRole("list", { name: "Resultats de la cerca" })).toHaveCount(0);
      await expect(page.getByRole("navigation", { name: "Pàgines de resultats" })).toHaveCount(0);
    });

    test("no mostra el missatge quan hi ha resultats", async ({ page }) => {
      await simulaCerca(page, 200, resposta(llibres));
      await page.goto("/cerca?q=Rodoreda");

      await expect(targetes(page)).toHaveCount(2);
      await expect(page.getByText(MISSATGE)).toHaveCount(0);
    });

    test("no mostra el missatge si la cerca falla", async ({ page }) => {
      await simulaCerca(page, 500, {});
      await page.goto("/cerca?q=Rodoreda");

      await expect(page.getByRole("alert")).toBeVisible();
      await expect(page.getByText(MISSATGE)).toHaveCount(0);
    });

    test("no mostra el missatge si no s'ha cercat res", async ({ page }) => {
      await simulaCerca(page, 200, resposta([]));
      await page.goto("/cerca");

      await expect(page.getByText(MISSATGE)).toHaveCount(0);
    });
  });
});
