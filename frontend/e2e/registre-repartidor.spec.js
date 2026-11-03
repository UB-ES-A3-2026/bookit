import { test, expect } from "@playwright/test";

// Tests E2E del formulari de registre de repartidor (US1.1-T8), de la seva validació al client (US1.1-T9), de
// l'enviament a l'API (US1.1-T10) i de la pantalla de confirmació (US1.1-T11).
//
// L'endpoint del backend encara no existeix (US1.1-T4), així que els tests de l'enviament simulen les respostes
// de l'API tal com les descriu docs/api-registre-repartidor.md.

const URL_REGISTRE_API = "/api/auth/register/repartidor/";
const URL_CONFIRMACIO = "/registre/confirmacio";

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

test("si el formulari té errors no es crida l'API", async ({ page }) => {
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
});

// Respon a les peticions a l'endpoint de registre amb l'estat i el cos indicats, i guarda les dades que s'hi
// envien. El frontend i l'API són en ports diferents, per això cal respondre també la petició prèvia de CORS.
const CAPCALERES_CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
};

async function simulaApi(page, estat, cos = {}) {
  const enviades = [];
  await page.route(`**${URL_REGISTRE_API}`, async (ruta) => {
    if (ruta.request().method() === "OPTIONS") {
      await ruta.fulfill({ status: 204, headers: CAPCALERES_CORS });
      return;
    }
    enviades.push(ruta.request().postDataJSON());
    await ruta.fulfill({ status: estat, headers: CAPCALERES_CORS, json: cos });
  });
  return enviades;
}

test.describe("enviament a l'API (US1.1-T10)", () => {
  test("envia les dades del repartidor i, si el registre és correcte, mostra la confirmació", async ({ page }) => {
    const enviades = await simulaApi(page, 201, { id: 1, rol: "repartidor", estat: "pendent" });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    expect(enviades).toEqual([
      {
        nom: "Pol",
        cognoms: "Ferrer Soler",
        correu: "repartidor@example.com",
        dni: "12345678Z",
        telefon: "+34 612 345 678",
        vehicle: "moto",
        matricula: "1234 BCD",
        num_seguretat_social: "28/12345678/90",
        contrasenya: "Llibres-de-tardor-24",
      },
    ]);
  });

  test("amb bicicleta no s'envia la matrícula", async ({ page }) => {
    const enviades = await simulaApi(page, 201);
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides(), "Bicicleta");

    await botoEnviar(page).click();

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    expect(enviades).toHaveLength(1);
    expect(enviades[0].vehicle).toBe("bici");
    expect(enviades[0]).not.toHaveProperty("matricula");
  });

  test("mentre s'envia, el botó queda desactivat", async ({ page }) => {
    let respon;
    const resposta = new Promise((resolve) => {
      respon = resolve;
    });
    await page.route(`**${URL_REGISTRE_API}`, async (ruta) => {
      await resposta;
      await ruta.fulfill({ status: 201, headers: CAPCALERES_CORS, json: {} });
    });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    const botoEnviant = page.getByRole("button", { name: "Registrant..." });
    await expect(botoEnviant).toBeDisabled();
    respon();
    await expect(page).toHaveURL(URL_CONFIRMACIO);
  });

  test("si el correu o el DNI ja existeixen, es mostra l'error sota cada camp", async ({ page }) => {
    await simulaApi(page, 400, {
      correu: ["DNI/correu ja registrat"],
      dni: ["DNI/correu ja registrat"],
    });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(camp(page, "Correu electrònic")).toHaveAccessibleDescription("DNI/correu ja registrat");
    await expect(camp(page, "DNI / NIE")).toHaveAccessibleDescription("DNI/correu ja registrat");
    await expect(camp(page, "DNI / NIE")).toHaveAttribute("aria-invalid", "true");
    await expect(page).toHaveURL("/registre");
  });

  test("els errors dels camps amb nom diferent a l'API van al camp que toca", async ({ page }) => {
    await simulaApi(page, 400, {
      num_seguretat_social: ["El número de la Seguretat Social ha de tenir 12 xifres"],
      contrasenya: ["Aquesta contrasenya és massa comuna."],
    });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(camp(page, "Número de la Seguretat Social")).toHaveAccessibleDescription(
      "El número de la Seguretat Social ha de tenir 12 xifres",
    );
    await expect(camp(page, "Contrasenya")).toHaveAccessibleDescription("Aquesta contrasenya és massa comuna.");
  });

  test("en tornar a escriure en un camp se n'esborra l'error del backend", async ({ page }) => {
    await simulaApi(page, 400, { correu: ["DNI/correu ja registrat"] });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());
    await botoEnviar(page).click();
    await expect(camp(page, "Correu electrònic")).toHaveAccessibleDescription("DNI/correu ja registrat");

    await camp(page, "Correu electrònic").fill("un-altre@example.com");

    await expect(camp(page, "Correu electrònic")).toHaveAccessibleDescription("");
  });

  test("un error que no és de cap camp es mostra com a error general", async ({ page }) => {
    await simulaApi(page, 400, { non_field_errors: ["Error inesperat"] });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(page.getByText("No s'ha pogut completar el registre. Revisa les dades")).toBeVisible();
    await expect(page).toHaveURL("/registre");
  });

  test("si el backend falla, es demana tornar-ho a provar més tard", async ({ page }) => {
    await simulaApi(page, 500);
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(page.getByText("Torna-ho a provar més tard")).toBeVisible();
    await expect(botoEnviar(page)).toBeEnabled();
    await expect(page).toHaveURL("/registre");
  });
});

test.describe("pantalla de confirmació (US1.1-T11)", () => {
  const titolConfirmacio = (page) => page.getByRole("heading", { level: 1 });

  test("després del registre diu que el compte queda pendent de validació", async ({ page }) => {
    await simulaApi(page, 201, { id: 1, rol: "repartidor", estat: "pendent" });
    await obrirFormulariRepartidor(page);
    await omplir(page, dadesValides());

    await botoEnviar(page).click();

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    await expect(titolConfirmacio(page)).toHaveText("Gràcies, Pol");
    await expect(page.getByText("Hem rebut la teva sol·licitud")).toBeVisible();
    await expect(page.getByText("Pendent de validació")).toBeVisible();
  });

  test("si s'obre directament, es mostra sense el nom", async ({ page }) => {
    await page.goto(URL_CONFIRMACIO);

    await expect(titolConfirmacio(page)).toHaveText("Gràcies per registrar-te");
    await expect(page.getByText("Pendent de validació")).toBeVisible();
  });

  test("el botó torna a la pàgina d'inici", async ({ page }) => {
    await page.goto(URL_CONFIRMACIO);

    await page.getByRole("link", { name: "Tornar a l'inici" }).click();

    await expect(page).toHaveURL("/");
  });

  test.describe("en mòbil", () => {
    test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

    test("la caixa es veu sencera sense desplaçament horitzontal", async ({ page }) => {
      await page.goto(URL_CONFIRMACIO);

      await expect(page.getByRole("link", { name: "Tornar a l'inici" })).toBeInViewport({ ratio: 1 });
      const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(ampladaPagina).toBeLessThanOrEqual(375);
    });
  });
});
