import { test, expect } from "@playwright/test";

// Tests E2E del registre de repartidor (US1.1-T15).
//
// Execució local, des de frontend/:
//   npm run test:e2e -- registre-repartidor-us1.1.spec.js
//
// Cal tenir en marxa:
//   docker compose up -d --build --wait
//
// Els tests de registre utilitzen l'API real i generen dades úniques.
// Els tests de validació posterior queden fixme perquè actualment no hi ha
// cap endpoint E2E per validar o rebutjar una sol·licitud.

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const URL_REGISTRE_API = "/api/auth/register/repartidor/";
const URL_CONFIRMACIO = "/registre/confirmacio";

const OBLIGATORI = "Aquest camp és obligatori.";
const CORREU_DUPLICAT = "DNI/correu ja registrat";

const CAMPS = {
  correu: "Correu electrònic",
  nom: "Nom",
  cognoms: "Cognoms",
  dni: "DNI / NIE",
  telefon: "Telèfon",
  vehicle: "Tipus de vehicle",
  matricula: "Matrícula",
  seguretatSocial: "Número de la Seguretat Social",
  contrasenya: "Contrasenya",
  confirmarContrasenya: "Confirmar contrasenya",
};

const camp = (page, nom) => page.getByLabel(CAMPS[nom], { exact: true });
const botoEnviar = (page) =>
  page.getByRole("button", { name: "Completar Registre", exact: true });

function identificadorUnic() {
  return `${Date.now()}${Math.floor(Math.random() * 1e6)}`;
}

function lletraDni(numero) {
  return "TRWAGMYFPDXBNJZSQVHLCKE"[numero % 23];
}

function dniUnic() {
  const numero = Number(identificadorUnic().slice(-8));
  return `${String(numero).padStart(8, "0")}${lletraDni(numero)}`;
}

function dadesNoves(canvis = {}) {
  const id = identificadorUnic();

  return {
    correu: `repartidor.e2e.${id}@example.com`,
    nom: `Repartidor E2E ${id}`,
    cognoms: "Prova E2E",
    dni: dniUnic(),
    telefon: "612345678",
    vehicle: "moto",
    matricula: "1234 BCD",
    num_seguretat_social: `28${id.slice(-10)}`,
    contrasenya: "Llibres-de-tardor-24",
    confirmarContrasenya: "Llibres-de-tardor-24",
    ...canvis,
  };
}

async function obrirFormulari(page) {
  await page.goto("/registre");
  await page.getByRole("button", { name: "Repartidor", exact: true }).click();

  await expect(
    page.getByRole("button", {
      name: "Repartidor",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(camp(page, "correu")).toBeVisible();
}

async function omplirFormulari(page, dades) {
  await camp(page, "correu").fill(dades.correu);
  await camp(page, "nom").fill(dades.nom);
  await camp(page, "cognoms").fill(dades.cognoms);
  await camp(page, "dni").fill(dades.dni);
  await camp(page, "telefon").fill(dades.telefon);
  await camp(page, "vehicle").selectOption(dades.vehicle);
  await camp(page, "matricula").fill(dades.matricula);
  await camp(page, "seguretatSocial").fill(dades.num_seguretat_social);
  await camp(page, "contrasenya").fill(dades.contrasenya);
  await camp(page, "confirmarContrasenya").fill(dades.confirmarContrasenya);
}

async function enviarFormulari(page) {
  return Promise.all([
    page.waitForResponse(
      (resposta) =>
        resposta.url().endsWith(URL_REGISTRE_API) &&
        resposta.request().method() === "POST",
    ),
    botoEnviar(page).click(),
  ]);
}

async function crearCompte(request, canvis = {}) {
  const dades = dadesNoves(canvis);

  const resposta = await request.post(`${API_URL}${URL_REGISTRE_API}`, {
    data: dades,
  });

  expect(resposta.status()).toBe(201);
  return dades;
}

test.describe("formulari de registre de repartidor (US1.1)", () => {
  test("CP-US1.1-01 · mostra els camps obligatoris", async ({ page }) => {
    await obrirFormulari(page);

    for (const nom of Object.keys(CAMPS)) {
      if (nom === "matricula") continue;
      await expect(camp(page, nom), nom).toBeVisible();
    }

    await camp(page, "vehicle").selectOption("moto");
    await expect(camp(page, "matricula")).toBeVisible();
  });

  test("CP-US1.1-02 · registre correcte amb moto i confirmació", async ({
    page,
  }) => {
    const dades = dadesNoves();

    await obrirFormulari(page);
    await omplirFormulari(page, dades);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(201);
    expect((await resposta.json()).estat).toBe("pendent");

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    await expect(page.getByText("Sol·licitud enviada")).toBeVisible();
    await expect(
      page.getByText(
        "Hem rebut la teva sol·licitud per ser repartidor de bookit.",
      ),
    ).toBeVisible();
    await expect(page.getByText("Pendent de validació")).toBeVisible();
  });

  test("CP-US1.1-03 · registre correcte amb bicicleta sense matrícula", async ({
    page,
  }) => {
    const dades = dadesNoves({
      dni: "X1234567L",
      vehicle: "bici",
      matricula: "",
    });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);

    await expect(camp(page, "matricula")).toBeHidden();

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(201);
    expect((await resposta.json()).vehicle).toBe("bici");
    expect((await resposta.json()).matricula).toBe("");

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    await expect(page.getByText("Pendent de validació")).toBeVisible();
  });

  test("CP-US1.1-04 · formulari buit mostra els camps obligatoris", async ({
    page,
  }) => {
    await obrirFormulari(page);

    await botoEnviar(page).click();

    for (const nom of [
      "correu",
      "nom",
      "cognoms",
      "dni",
      "telefon",
      "vehicle",
      "seguretatSocial",
      "contrasenya",
      "confirmarContrasenya",
    ]) {
      await expect(camp(page, nom), nom).toHaveAccessibleDescription(
        OBLIGATORI,
      );
    }

    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-05 · nom buit mostra un error inline", async ({ page }) => {
    const dades = dadesNoves({ nom: "" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "nom")).toHaveAccessibleDescription(OBLIGATORI);
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-06 · cognoms buits mostren un error inline", async ({
    page,
  }) => {
    const dades = dadesNoves({ cognoms: "" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "cognoms")).toHaveAccessibleDescription(OBLIGATORI);
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-07 · correu amb format invàlid", async ({ page }) => {
    const dades = dadesNoves({ correu: "repartidor@" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "correu")).toHaveAccessibleDescription(
      /El correu ha de ser una adreça vàlida/,
    );
    await expect(camp(page, "correu")).toHaveAttribute("aria-invalid", "true");
  });

  test("CP-US1.1-08 · telèfon amb format invàlid", async ({ page }) => {
    const dades = dadesNoves({ telefon: "512345678" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "telefon")).toHaveAccessibleDescription(
      /El telèfon ha de tenir 9 xifres/,
    );
    await expect(camp(page, "telefon")).toHaveAttribute("aria-invalid", "true");
  });

  test("CP-US1.1-09 · DNI amb format invàlid", async ({ page }) => {
    const dades = dadesNoves({ dni: "12345678A" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "dni")).toHaveAccessibleDescription(
      /El DNI\/NIE no és vàlid/,
    );
    await expect(camp(page, "dni")).toHaveAttribute("aria-invalid", "true");
  });

  test("CP-US1.1-10 · correu duplicat", async ({ page, request }) => {
    const existent = await crearCompte(request);
    const dades = dadesNoves({ correu: existent.correu });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(400);
    await expect(camp(page, "correu")).toHaveAccessibleDescription(
      CORREU_DUPLICAT,
    );
    await expect(page).toHaveURL("/registre");
    await expect(page.getByText("Pendent de validació")).toBeHidden();
  });

  test("CP-US1.1-11 · DNI duplicat", async ({ page, request }) => {
    const existent = await crearCompte(request);
    const dades = dadesNoves({ dni: existent.dni });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(400);
    await expect(camp(page, "dni")).toHaveAccessibleDescription(
      CORREU_DUPLICAT,
    );
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-12 · correu i DNI duplicats", async ({ page, request }) => {
    const existent = await crearCompte(request);
    const dades = dadesNoves({
      correu: existent.correu,
      dni: existent.dni,
    });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(400);
    await expect(camp(page, "correu")).toHaveAccessibleDescription(
      CORREU_DUPLICAT,
    );
    await expect(camp(page, "dni")).toHaveAccessibleDescription(
      CORREU_DUPLICAT,
    );
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-14 · matrícula absent per a moto", async ({ page }) => {
    const dades = dadesNoves({ matricula: "" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "matricula")).toHaveAccessibleDescription(
      OBLIGATORI,
    );
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-15 · matrícula amb format invàlid", async ({ page }) => {
    const dades = dadesNoves({ matricula: "1234 ABC" });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "matricula")).toHaveAccessibleDescription(
      /La matrícula ha de tenir 4 xifres i 3 lletres/,
    );
    await expect(camp(page, "matricula")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  test("CP-US1.1-16 · Seguretat Social amb format invàlid", async ({
    page,
  }) => {
    const dades = dadesNoves({
      num_seguretat_social: "28123456789",
    });

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await botoEnviar(page).click();

    await expect(camp(page, "seguretatSocial")).toHaveAccessibleDescription(
      /El número de la Seguretat Social ha de tenir 12 xifres/,
    );
    await expect(camp(page, "seguretatSocial")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  test("CP-US1.1-17 · mostra els errors inline sota els camps afectats", async ({
    page,
  }) => {
    await obrirFormulari(page);
    await botoEnviar(page).click();

    const campNom = camp(page, "nom");
    const errorNom = page.locator("#repartidor-nom-error");

    await expect(campNom).toHaveAccessibleDescription(OBLIGATORI);
    await expect(errorNom).toBeVisible();

    const campBox = await campNom.boundingBox();
    const errorBox = await errorNom.boundingBox();

    expect(errorBox.y).toBeGreaterThan(campBox.y);
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.1-18 · mostra la confirmació pendent de validació", async ({
    page,
  }) => {
    const dades = dadesNoves();

    await obrirFormulari(page);
    await omplirFormulari(page, dades);
    await enviarFormulari(page);

    await expect(page).toHaveURL(URL_CONFIRMACIO);
    await expect(page.getByText("Sol·licitud enviada")).toBeVisible();
    await expect(page.getByText("Pendent de validació")).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Tornar a l'inici" }),
    ).toBeVisible();
  });

  test.fixme("CP-US1.1-19 · inici de sessió amb un compte validat", async () => {
    // No existeix cap endpoint E2E per canviar el perfil a «validat».
    // Caldria exposar una fixture o endpoint de proves, o executar una
    // acció d'administració abans del login.
  });

  test.fixme("CP-US1.1-20 · inici de sessió amb un compte rebutjat", async () => {
    // No existeix cap endpoint E2E per canviar el perfil a «rebutjat».
    // Caldria exposar una fixture o endpoint de proves i implementar el
    // flux de login corresponent.
  });
});
