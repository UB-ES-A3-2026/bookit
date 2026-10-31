import { test, expect } from "@playwright/test";

// Tests E2E del formulari de registre de repartidor (US1.1-T8) i de la seva validació al client (US1.1-T9).
// L'enviament a l'API és la US1.1-T10; de moment es comprova que no se'n fa cap petició.

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

const botoEnviar = (page) => page.getByRole("button", { name: "Completar Registre" });
const OBLIGATORI = "Aquest camp és obligatori.";

async function obrirFormulariRepartidor(page) {
  await page.goto("/registre");
  await tipusCompte(page, "Repartidor").click();
}

// Dades correctes de repartidor; cada test en canvia les que li calen.
function dadesValides(canvis = {}) {
  return {
    "Correu electrònic": "repartidor@example.com",
    Nom: "Pol",
    Cognoms: "Ferrer Soler",
    "DNI / NIE": "12345678Z",
    Telèfon: "+34 612 345 678",
    Matrícula: "1234 BCD",
    "Número de la Seguretat Social": "28/12345678/90",
    Contrasenya: "Llibres-de-tardor-24",
    "Confirmar contrasenya": "Llibres-de-tardor-24",
    ...canvis,
  };
}

async function omplir(page, dades, vehicle = "Moto") {
  await camp(page, "Tipus de vehicle").selectOption({ label: vehicle });
  for (const [etiqueta, valor] of Object.entries(dades)) {
    if (etiqueta === "Matrícula" && vehicle === "Bicicleta") continue;
    await camp(page, etiqueta).fill(valor);
  }
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

  await botoEnviar(page).click();

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

test.describe("validació al client (US1.1-T9)", () => {
  test("enviar el formulari buit mostra els camps obligatoris", async ({ page }) => {
    await obrirFormulariRepartidor(page);

    await botoEnviar(page).click();

    for (const etiqueta of CAMPS) {
      await expect(camp(page, etiqueta), etiqueta).toHaveAccessibleDescription(OBLIGATORI);
    }
    await expect(page).toHaveURL("/registre");
  });

  test("amb moto o cotxe la matrícula és obligatòria", async ({ page }) => {
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides({ Matrícula: "" }), "Cotxe");

    await botoEnviar(page).click();

    await expect(matricula(page)).toHaveAccessibleDescription(OBLIGATORI);
  });

  test("amb bicicleta no es demana la matrícula", async ({ page }) => {
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides(), "Bicicleta");

    await botoEnviar(page).click();

    for (const etiqueta of CAMPS) {
      await expect(camp(page, etiqueta), etiqueta).toHaveAccessibleDescription("");
    }
  });

  for (const [etiqueta, valor, error] of [
    ["Correu electrònic", "repartidor@", "El correu ha de ser una adreça vàlida"],
    ["DNI / NIE", "12345678A", "El DNI/NIE no és vàlid"],
    ["DNI / NIE", "1234567Z", "El DNI/NIE no és vàlid"],
    ["Telèfon", "612 345", "El telèfon ha de tenir 9 xifres"],
    ["Telèfon", "512 345 678", "El telèfon ha de tenir 9 xifres"],
    ["Matrícula", "1234 ABC", "La matrícula ha de tenir 4 xifres i 3 lletres"],
    ["Número de la Seguretat Social", "28/1234", "ha de tenir 12 xifres"],
    ["Confirmar contrasenya", "Una-altra-contrasenya-1", "Les contrasenyes no coincideixen"],
  ]) {
    test(`${etiqueta} "${valor}" mostra un error de format`, async ({ page }) => {
      await obrirFormulariRepartidor(page);
      await omplir(page, dadesValides({ [etiqueta]: valor }));

      await botoEnviar(page).click();

      await expect(camp(page, etiqueta)).toHaveAccessibleDescription(new RegExp(error));
      await expect(camp(page, etiqueta)).toHaveAttribute("aria-invalid", "true");
    });
  }

  test("accepta un NIE i un telèfon sense prefix", async ({ page }) => {
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides({ "DNI / NIE": "X1234567L", Telèfon: "612345678" }));

    await botoEnviar(page).click();

    await expect(camp(page, "DNI / NIE")).toHaveAccessibleDescription("");
    await expect(camp(page, "Telèfon")).toHaveAccessibleDescription("");
  });

  test("en tornar a escriure en un camp se n'esborra l'error", async ({ page }) => {
    await obrirFormulariRepartidor(page);
    await botoEnviar(page).click();
    await expect(camp(page, "Nom")).toHaveAccessibleDescription(OBLIGATORI);

    await camp(page, "Nom").fill("Pol");

    await expect(camp(page, "Nom")).toHaveAccessibleDescription("");
    await expect(camp(page, "Cognoms")).toHaveAccessibleDescription(OBLIGATORI);
  });

  test("amb totes les dades correctes no hi ha cap error ni es crida l'API", async ({ page }) => {
    const peticions = [];
    page.on("request", (peticio) => {
      if (peticio.url().endsWith(URL_REGISTRE_API)) peticions.push(peticio);
    });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    for (const etiqueta of [...CAMPS, "Matrícula"]) {
      await expect(camp(page, etiqueta), etiqueta).toHaveAccessibleDescription("");
    }
    await expect(page).toHaveURL("/registre");
    expect(peticions).toEqual([]);
  });
});
