import { test, expect } from "@playwright/test";

// Tests E2E del formulari de registre de repartidor (US1.1-T8).
// La validació al client és la US1.1-T9 i l'enviament a l'API, la US1.1-T10; aquí només es comprova el formulari.

const URL_REGISTRE_API = "/api/auth/register/";

const CAMPS = [
  "Correu electrònic",
  "Nom",
  "Cognoms",
  "DNI / NIE",
  "Telèfon",
  "Tipus de vehicle",
  "Número de la Seguretat Social",
  "Contrasenya",
  "Confirmar contrasenya",
];

const camp = (page, etiqueta) => page.getByLabel(etiqueta, { exact: true });
const matricula = (page) => camp(page, "Matrícula");
const tipusCompte = (page, nom) => page.getByRole("button", { name: nom, exact: true });

async function obrirFormulariRepartidor(page) {
  await page.goto("/registre");
  await tipusCompte(page, "Repartidor").click();
}

test("en triar Repartidor es mostra el formulari de repartidor", async ({ page }) => {
  await obrirFormulariRepartidor(page);

  await expect(tipusCompte(page, "Repartidor")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Funcionalitat no implementada")).toBeHidden();
  for (const etiqueta of CAMPS) {
    await expect(camp(page, etiqueta), etiqueta).toBeVisible();
  }
  // Els camps propis del lector no hi són.
  await expect(camp(page, "Adreça física")).toBeHidden();
  await expect(camp(page, "Número de carnet de biblioteca")).toBeHidden();
});

test("el tipus de vehicle té les opcions bicicleta, moto i cotxe", async ({ page }) => {
  await obrirFormulariRepartidor(page);

  await expect(camp(page, "Tipus de vehicle")).toHaveValue("");
  await expect(camp(page, "Tipus de vehicle").locator("option:not([disabled])")).toHaveText([
    "Bicicleta",
    "Moto",
    "Cotxe",
  ]);
});

test("la matrícula només es demana per a moto i cotxe", async ({ page }) => {
  await obrirFormulariRepartidor(page);
  await expect(matricula(page)).toBeHidden();

  for (const vehicle of ["Moto", "Cotxe"]) {
    await camp(page, "Tipus de vehicle").selectOption({ label: vehicle });
    await expect(matricula(page), vehicle).toBeVisible();
  }

  await camp(page, "Tipus de vehicle").selectOption({ label: "Bicicleta" });
  await expect(matricula(page)).toBeHidden();
});

test("en canviar a bicicleta s'esborra la matrícula escrita", async ({ page }) => {
  await obrirFormulariRepartidor(page);
  await camp(page, "Tipus de vehicle").selectOption({ label: "Cotxe" });
  await matricula(page).fill("1234 BCD");

  await camp(page, "Tipus de vehicle").selectOption({ label: "Bicicleta" });
  await camp(page, "Tipus de vehicle").selectOption({ label: "Moto" });

  await expect(matricula(page)).toHaveValue("");
});

test("tornar a Lector mostra el formulari de lector", async ({ page }) => {
  await obrirFormulariRepartidor(page);

  await tipusCompte(page, "Lector").click();

  await expect(camp(page, "Adreça física")).toBeVisible();
  await expect(camp(page, "Tipus de vehicle")).toBeHidden();
});

test("enviar el formulari de repartidor encara no crida l'API", async ({ page }) => {
  const peticions = [];
  page.on("request", (peticio) => {
    if (peticio.url().endsWith(URL_REGISTRE_API)) peticions.push(peticio);
  });
  await obrirFormulariRepartidor(page);

  await page.getByRole("button", { name: "Completar Registre" }).click();

  await expect(page).toHaveURL("/registre");
  expect(peticions).toEqual([]);
});

test.describe("en mòbil", () => {
  test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

  test("tots els camps es veuen sencers sense desplaçament horitzontal", async ({ page }) => {
    await obrirFormulariRepartidor(page);
    await camp(page, "Tipus de vehicle").selectOption({ label: "Moto" });

    for (const etiqueta of [...CAMPS, "Matrícula"]) {
      const element = camp(page, etiqueta);
      await element.scrollIntoViewIfNeeded();
      await expect(element, etiqueta).toBeInViewport({ ratio: 1 });
    }
    const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(ampladaPagina).toBeLessThanOrEqual(375);
  });
});
