import { test, expect } from "@playwright/test";

// Tests E2E del registre de biblioteca (US1.2-T15).
// Requereixen el frontend i el backend en marxa, amb la base de dades migrada.
// El correu de verificació s'imprimeix a la consola del backend. Com que Playwright
// no pot llegir aquesta consola ni existeix cap bústia de proves, la verificació
// del compte queda marcada amb test.fixme.

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const URL_REGISTRE_BIBLIOTECA = "/api/auth/register/biblioteca/";

const MISSATGE_CAMP_INVALID =
  "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho";

const MISSATGE_CORREU_DUPLICAT =
  "Aquest correu correspon a un compte existent, torna a probar amb un altre correu";

function dadesNoves() {
  const identificador = `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

  return {
    nom: `Biblioteca E2E ${identificador}`,
    correu: `biblioteca.e2e.${identificador}@example.com`,
    dniNie: "12345678Z",
  };
}

function botoBiblioteca(page) {
  return page.getByRole("button", {
    name: "Biblioteca",
    exact: true,
  });
}

function campBiblioteca(page, nom) {
  const camps = {
    correu: "Correu electrònic oficial",
    nom: "Nom de la biblioteca",
    dniNie: "DNI / NIE del responsable",
  };

  return page.getByLabel(camps[nom], { exact: true });
}

function botoEnviar(page) {
  return page.getByRole("button", {
    name: "Completar Registre",
    exact: true,
  });
}

async function obrirRegistreBiblioteca(page) {
  await page.goto("/");
  await page.getByRole("link", { name: "Registra't" }).click();

  await expect(page).toHaveURL("/registre");
  await expect(
    page.getByRole("heading", { name: "Crear un compte" }),
  ).toBeVisible();

  await botoBiblioteca(page).click();
  await expect(campBiblioteca(page, "correu")).toBeVisible();
  await expect(campBiblioteca(page, "nom")).toBeVisible();
}

async function omplirFormulariBiblioteca(page, dades) {
  await campBiblioteca(page, "correu").fill(dades.correu);
  await campBiblioteca(page, "nom").fill(dades.nom);

  // El frontend actual exigeix aquest camp, tot i que no forma part dels CA de la US1.2.
  await campBiblioteca(page, "dniNie").fill(dades.dniNie);
}

async function enviarFormulari(page) {
  return Promise.all([
    page.waitForResponse(
      (resposta) =>
        resposta.url().endsWith(URL_REGISTRE_BIBLIOTECA) &&
        resposta.request().method() === "POST",
    ),
    botoEnviar(page).click(),
  ]);
}

test.describe("registre de biblioteca (US1.2)", () => {
  test.fixme('CP-US1.2-01 · mostra el botó "Registrar-se com a biblioteca"', async ({
    page,
  }) => {
    await page.goto("/");

    await expect(
      page.getByRole("button", {
        name: "Registrar-se com a biblioteca",
        exact: true,
      }),
    ).toBeVisible();
  });

  test("CP-US1.2-02 · mostra els camps obligatoris", async ({ page }) => {
    await obrirRegistreBiblioteca(page);

    await expect(campBiblioteca(page, "nom")).toBeVisible();
    await expect(campBiblioteca(page, "correu")).toBeVisible();
  });

  test("CP-US1.2-03 · rebutja el formulari sense el nom", async ({ page }) => {
    await obrirRegistreBiblioteca(page);

    const peticions = [];
    page.on("request", (peticio) => {
      if (
        peticio.url().endsWith(URL_REGISTRE_BIBLIOTECA) &&
        peticio.method() === "POST"
      ) {
        peticions.push(peticio);
      }
    });

    const dades = dadesNoves();
    await campBiblioteca(page, "correu").fill(dades.correu);
    await campBiblioteca(page, "dniNie").fill(dades.dniNie);
    await botoEnviar(page).click();

    await expect(
      page.getByText(MISSATGE_CAMP_INVALID, { exact: true }),
    ).toBeVisible();
    await expect(page).toHaveURL("/registre");
    expect(peticions).toHaveLength(0);
  });

  test("CP-US1.2-04 · rebutja el formulari sense el correu", async ({
    page,
  }) => {
    await obrirRegistreBiblioteca(page);

    const peticions = [];
    page.on("request", (peticio) => {
      if (
        peticio.url().endsWith(URL_REGISTRE_BIBLIOTECA) &&
        peticio.method() === "POST"
      ) {
        peticions.push(peticio);
      }
    });

    const dades = dadesNoves();
    await campBiblioteca(page, "nom").fill(dades.nom);
    await campBiblioteca(page, "dniNie").fill(dades.dniNie);
    await botoEnviar(page).click();

    await expect(
      page.getByText(MISSATGE_CAMP_INVALID, { exact: true }),
    ).toBeVisible();
    await expect(page).toHaveURL("/registre");
    expect(peticions).toHaveLength(0);
  });

  test("CP-US1.2-05 · rebutja un correu amb format invàlid", async ({
    page,
  }) => {
    await obrirRegistreBiblioteca(page);

    const peticions = [];
    page.on("request", (peticio) => {
      if (
        peticio.url().endsWith(URL_REGISTRE_BIBLIOTECA) &&
        peticio.method() === "POST"
      ) {
        peticions.push(peticio);
      }
    });

    const dades = dadesNoves();
    await campBiblioteca(page, "correu").fill("correu-invalid");
    await campBiblioteca(page, "nom").fill(dades.nom);
    await campBiblioteca(page, "dniNie").fill(dades.dniNie);
    await botoEnviar(page).click();

    await expect(
      page.getByText(MISSATGE_CAMP_INVALID, { exact: true }),
    ).toBeVisible();
    await expect(page).toHaveURL("/registre");
    expect(peticions).toHaveLength(0);
  });

  test("CP-US1.2-06 · registra una biblioteca correctament", async ({
    page,
  }) => {
    const dades = dadesNoves();

    await obrirRegistreBiblioteca(page);
    await omplirFormulariBiblioteca(page, dades);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(201);
    expect(await resposta.json()).toEqual({
      nom: dades.nom,
      correu: dades.correu,
    });

    await expect(
      page.getByRole("heading", { name: "Revisa el teu correu" }),
    ).toBeVisible();
    await expect(page.getByText(dades.correu, { exact: true })).toBeVisible();
    await expect(page).toHaveURL("/registre");
  });

  test("CP-US1.2-07 · rebutja un correu ja registrat", async ({
    page,
    request,
  }) => {
    const existent = dadesNoves();

    const primeraResposta = await request.post(
      `${API_URL}${URL_REGISTRE_BIBLIOTECA}`,
      {
        data: {
          nom: existent.nom,
          correu: existent.correu,
        },
      },
    );

    expect(primeraResposta.status()).toBe(201);

    await obrirRegistreBiblioteca(page);

    const dades = dadesNoves();
    await campBiblioteca(page, "nom").fill(dades.nom);
    await campBiblioteca(page, "correu").fill(existent.correu);
    await campBiblioteca(page, "dniNie").fill(dades.dniNie);

    const [resposta] = await enviarFormulari(page);

    expect(resposta.status()).toBe(400);
    await expect(
      page.getByText(MISSATGE_CORREU_DUPLICAT, { exact: true }),
    ).toBeVisible();
    await expect(page).toHaveURL("/registre");
  });

  test.fixme("CP-US1.2-08 · el compte continua inactiu abans de verificar el correu", async () => {
    // No hi ha cap superfície observable des del navegador per consultar
    // l'estat is_active del compte abans de verificar-lo.
  });

  test.fixme("CP-US1.2-09 · verifica el compte amb l'enllaç del correu", async ({
    page,
  }) => {
    // El backend imprimeix l'enllaç a la consola del contenidor mitjançant
    // console.EmailBackend. No hi ha cap bústia de proves, endpoint per
    // recuperar el correu ni fixture de Playwright per llegir aquesta sortida.
    // Caldria exposar una bústia de proves o un mecanisme segur per obtenir
    // l'enllaç abans de poder automatitzar aquest cas.
    await page.goto("/registre");
  });
});

// Pàgina de verificació: la biblioteca tria la contrasenya en obrir l'enllaç del correu.
// L'API es simula amb page.route perquè l'enllaç real només surt al correu.
test.describe("triar la contrasenya en verificar el compte", () => {
  const RUTA = "/verificacio/biblioteca/MQ/token-de-prova";
  const URL_API = "**/api/auth/verify/biblioteca/MQ/token-de-prova/";
  const CAPCALERES_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
  };

  // Respon el GET (comprovació de l'enllaç) i el POST (contrasenya) de la verificació.
  async function simulaVerificacio(page, { get, post }) {
    const enviades = [];
    await page.route(URL_API, async (route) => {
      const peticio = route.request();
      if (peticio.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: CAPCALERES_CORS });
        return;
      }
      if (peticio.method() === "POST") {
        enviades.push(peticio.postDataJSON());
        await route.fulfill({ headers: CAPCALERES_CORS, ...post });
        return;
      }
      await route.fulfill({ headers: CAPCALERES_CORS, ...get });
    });
    return enviades;
  }

  const enllacValid = { status: 200, json: { correu: "biblioteca@example.com" } };
  const enllacInvalid = {
    status: 400,
    json: { detail: "L'enllaç de verificació no és vàlid o ha caducat." },
  };

  test("demana la contrasenya i activa el compte", async ({ page }) => {
    const enviades = await simulaVerificacio(page, {
      get: enllacValid,
      post: { status: 200, json: { detail: "El compte de biblioteca s'ha verificat correctament." } },
    });
    await page.goto(RUTA);

    await expect(page.getByText("biblioteca@example.com")).toBeVisible();
    await page.getByLabel("Contrasenya", { exact: true }).fill("Llibres-de-tardor-24");
    await page.getByLabel("Confirmar contrasenya", { exact: true }).fill("Llibres-de-tardor-24");
    await page.getByRole("button", { name: "Activar el compte" }).click();

    await expect(page.getByText("El compte de biblioteca s'ha verificat correctament.")).toBeVisible();
    expect(enviades).toEqual([{ contrasenya: "Llibres-de-tardor-24" }]);

    await page.getByRole("link", { name: "Iniciar sessió" }).click();
    await expect(page).toHaveURL("/inicia-sessio");
  });

  test("no envia res si les contrasenyes no coincideixen", async ({ page }) => {
    const enviades = await simulaVerificacio(page, { get: enllacValid, post: enllacValid });
    await page.goto(RUTA);

    await page.getByLabel("Contrasenya", { exact: true }).fill("Llibres-de-tardor-24");
    await page.getByLabel("Confirmar contrasenya", { exact: true }).fill("Una-altra-cosa-24");
    await page.getByRole("button", { name: "Activar el compte" }).click();

    await expect(page.getByText("Les contrasenyes no coincideixen.")).toBeVisible();
    expect(enviades).toEqual([]);
  });

  test("mostra el motiu si la contrasenya no és prou segura", async ({ page }) => {
    await simulaVerificacio(page, {
      get: enllacValid,
      post: {
        status: 400,
        json: { contrasenya: ["Aquesta contrasenya és massa curta. Ha de tenir com a mínim 8 caràcters."] },
      },
    });
    await page.goto(RUTA);

    await page.getByLabel("Contrasenya", { exact: true }).fill("curta1");
    await page.getByLabel("Confirmar contrasenya", { exact: true }).fill("curta1");
    await page.getByRole("button", { name: "Activar el compte" }).click();

    await expect(page.getByText(/massa curta/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Activar el compte" })).toBeVisible();
  });

  test("amb un enllaç caducat no demana la contrasenya", async ({ page }) => {
    await simulaVerificacio(page, { get: enllacInvalid, post: enllacInvalid });
    await page.goto(RUTA);

    await expect(page.getByRole("alert")).toContainText(
      "L'enllaç de verificació no és vàlid o ha caducat.",
    );
    await expect(page.getByLabel("Contrasenya", { exact: true })).toHaveCount(0);
  });
});
