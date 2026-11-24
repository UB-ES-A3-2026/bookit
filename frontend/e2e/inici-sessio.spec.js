import { test, expect } from "@playwright/test";

// Tests E2E de l'inici de sessió (US2-T15).
//
// Execució local:
//   npm run test:e2e -- inici-sessio.spec.js
//
// Cal tenir en marxa:
//   docker compose up -d --build --wait
//
// El backend ha d'estar migrat i el frontend ha de disposar de VITE_API_URL.
// Els tests creen les dades pròpies mitjançant els endpoints públics de registre.
// No s'utilitzen credencials fixes ni dades compartides entre tests.

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const URL_LOGIN = "/api/auth/login/";
const URL_ME = "/api/auth/me/";
const URL_REGISTRE = "/api/auth/register/";
const URL_REGISTRE_REPARTIDOR = "/api/auth/register/repartidor/";

const CONTRASENYA = "Llibres-de-tardor-24";
const MISSATGE_CREDENCIALS = "El correu o la contrasenya no són correctes.";
const MISSATGE_OBLIGATORI = "Aquest camp és obligatori.";

function identificadorUnic() {
  return `${Date.now()}${Math.floor(Math.random() * 1e6)}`;
}

function dadesUsuari() {
  const id = identificadorUnic();

  return {
    correu: `e2e.usuari.${id}@example.com`,
    nom: `Usuari E2E ${id}`,
    adreca: "C/ Major 1, 08001 Barcelona",
    num_carnet: String(id).slice(-10).padStart(10, "0"),
    contrasenya: CONTRASENYA,
  };
}

function dadesRepartidor() {
  const id = identificadorUnic();

  return {
    nom: `Repartidor E2E ${id}`,
    cognoms: "Prova E2E",
    correu: `e2e.repartidor.${id}@example.com`,
    dni: "12345678Z",
    telefon: "612345678",
    vehicle: "moto",
    matricula: "1234BCD",
    num_seguretat_social: "281234567890",
    contrasenya: CONTRASENYA,
  };
}

function campCorreu(page) {
  return page.getByLabel("Correu electrònic / Nom d'usuari", {
    exact: true,
  });
}

function campContrasenya(page) {
  return page.getByLabel("Contrasenya", { exact: true });
}

function botoEnviar(page) {
  return page.getByRole("button", {
    name: "Iniciar Sessió",
    exact: true,
  });
}

function modalLogin(page) {
  return page.getByRole("dialog", { name: "Inicia Sessió" });
}

async function obrirLogin(page) {
  await page.goto("/");
  await page.getByRole("link", { name: "Inicia sessió", exact: true }).click();

  await expect(page).toHaveURL("/inicia-sessio");
  await expect(modalLogin(page)).toBeVisible();
}

async function crearUsuari(request) {
  const dades = dadesUsuari();

  const resposta = await request.post(`${API_URL}${URL_REGISTRE}`, {
    data: dades,
  });

  expect(resposta.status()).toBe(201);
  return dades;
}

async function crearRepartidor(request) {
  const dades = dadesRepartidor();

  const resposta = await request.post(`${API_URL}${URL_REGISTRE_REPARTIDOR}`, {
    data: dades,
  });

  expect(resposta.status()).toBe(201);
  return dades;
}

async function omplirLogin(page, correu, contrasenya) {
  await campCorreu(page).fill(correu);
  await campContrasenya(page).fill(contrasenya);
}

async function enviarLogin(page) {
  return Promise.all([
    page.waitForResponse(
      (resposta) =>
        resposta.url().endsWith(URL_LOGIN) &&
        resposta.request().method() === "POST",
    ),
    botoEnviar(page).click(),
  ]);
}

test.describe("inici de sessió (US2)", () => {
  test("CP-US2-01 · inici de sessió correcte com a Usuari", async ({
    page,
    request,
  }) => {
    const dades = await crearUsuari(request);

    await obrirLogin(page);
    await omplirLogin(page, dades.correu, dades.contrasenya);

    const [respostaLogin] = await enviarLogin(page);

    expect(respostaLogin.status()).toBe(200);

    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("button", { name: "Tancar sessió", exact: true }),
    ).toBeVisible();
    await expect(page.getByText(dades.nom, { exact: true })).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Inicia sessió", exact: true }),
    ).toBeHidden();

    const sessio = await page.evaluate(() =>
      JSON.parse(sessionStorage.getItem("bookit.sessio")),
    );

    expect(sessio.rol).toBe("usuari");
    expect(sessio.accessToken).toBeTruthy();
    expect(sessio.refreshToken).toBeTruthy();
  });

  test.fixme("CP-US2-01 · inici de sessió correcte com a Repartidor", async ({
    page,
    request,
  }) => {
    const dades = await crearRepartidor(request);

    // El registre públic crea el perfil amb estat "pendent".
    // No existeix cap endpoint E2E per validar-lo abans del login.
    await obrirLogin(page);
    await omplirLogin(page, dades.correu, dades.contrasenya);

    const [respostaLogin] = await enviarLogin(page);

    expect(respostaLogin.status()).toBe(200);
    await expect(page).toHaveURL("/repartidor");
  });

  test.fixme("CP-US2-01 · inici de sessió correcte com a Biblioteca", async ({
    page,
  }) => {
    // En l'estat actual no existeix cap endpoint de registre de biblioteca
    // ni cap fixture accessible des de Playwright per crear una biblioteca
    // verificada.
    await obrirLogin(page);
    await omplirLogin(page, "biblioteca.e2e@example.com", CONTRASENYA);
    await enviarLogin(page);
    await expect(page).toHaveURL("/cataleg");
  });

  test("CP-US2-02 · correu inexistent mostra un error genèric", async ({
    page,
  }) => {
    await obrirLogin(page);
    await omplirLogin(
      page,
      `inexistent.${identificadorUnic()}@example.com`,
      CONTRASENYA,
    );

    const [respostaLogin] = await enviarLogin(page);

    expect(respostaLogin.status()).toBe(401);
    await expect(
      page.getByRole("alert").filter({ hasText: MISSATGE_CREDENCIALS }),
    ).toBeVisible();
    await expect(page).toHaveURL("/inicia-sessio");
    await expect(modalLogin(page)).toBeVisible();

    const sessio = await page.evaluate(() =>
      sessionStorage.getItem("bookit.sessio"),
    );
    expect(sessio).toBeNull();
  });

  test("CP-US2-03 · contrasenya incorrecta mostra el mateix error genèric", async ({
    page,
    request,
  }) => {
    const dades = await crearUsuari(request);

    await obrirLogin(page);
    await omplirLogin(page, dades.correu, `incorrecta-${identificadorUnic()}`);

    const [respostaLogin] = await enviarLogin(page);

    expect(respostaLogin.status()).toBe(401);
    await expect(
      page.getByRole("alert").filter({ hasText: MISSATGE_CREDENCIALS }),
    ).toBeVisible();
    await expect(page).toHaveURL("/inicia-sessio");
    await expect(modalLogin(page)).toBeVisible();

    const sessio = await page.evaluate(() =>
      sessionStorage.getItem("bookit.sessio"),
    );
    expect(sessio).toBeNull();
  });

  test("CP-US2-04 · el correu buit desactiva el botó", async ({ page }) => {
    await obrirLogin(page);
    await campContrasenya(page).fill(CONTRASENYA);

    await expect(botoEnviar(page)).toBeDisabled();
    await expect(page).toHaveURL("/inicia-sessio");

    const peticions = [];
    page.on("request", (peticio) => {
      if (peticio.url().endsWith(URL_LOGIN) && peticio.method() === "POST") {
        peticions.push(peticio);
      }
    });

    await botoEnviar(page).click({ force: true });
    expect(peticions).toHaveLength(0);
  });

  test("CP-US2-05 · la contrasenya buida desactiva el botó", async ({
    page,
  }) => {
    await obrirLogin(page);
    await campCorreu(page).fill(`usuari.${identificadorUnic()}@example.com`);

    await expect(botoEnviar(page)).toBeDisabled();
    await expect(page).toHaveURL("/inicia-sessio");

    const peticions = [];
    page.on("request", (peticio) => {
      if (peticio.url().endsWith(URL_LOGIN) && peticio.method() === "POST") {
        peticions.push(peticio);
      }
    });

    await botoEnviar(page).click({ force: true });
    expect(peticions).toHaveLength(0);
  });

  test("CP-US2-06 · tots els camps buits desactiven el botó", async ({
    page,
  }) => {
    await obrirLogin(page);

    await expect(campCorreu(page)).toHaveValue("");
    await expect(campContrasenya(page)).toHaveValue("");
    await expect(botoEnviar(page)).toBeDisabled();

    const peticions = [];
    page.on("request", (peticio) => {
      if (peticio.url().endsWith(URL_LOGIN) && peticio.method() === "POST") {
        peticions.push(peticio);
      }
    });

    await botoEnviar(page).click({ force: true });
    expect(peticions).toHaveLength(0);
    await expect(modalLogin(page)).toBeVisible();
  });

  test("CP-US2-07 · la contrasenya està emmascarada per defecte", async ({
    page,
  }) => {
    await obrirLogin(page);
    await campContrasenya(page).fill(CONTRASENYA);

    await expect(campContrasenya(page)).toHaveAttribute("type", "password");
    await expect(
      page.getByRole("button", { name: "Mostra la contrasenya" }),
    ).toBeVisible();
  });

  test("CP-US2-08 · mostra i oculta la contrasenya", async ({ page }) => {
    await obrirLogin(page);
    await campContrasenya(page).fill(CONTRASENYA);

    const botoMostra = page.getByRole("button", {
      name: "Mostra la contrasenya",
      exact: true,
    });

    await botoMostra.click();

    await expect(campContrasenya(page)).toHaveAttribute("type", "text");
    await expect(
      page.getByRole("button", {
        name: "Amaga la contrasenya",
        exact: true,
      }),
    ).toBeVisible();
    await expect(campContrasenya(page)).toHaveValue(CONTRASENYA);

    await page
      .getByRole("button", {
        name: "Amaga la contrasenya",
        exact: true,
      })
      .click();

    await expect(campContrasenya(page)).toHaveAttribute("type", "password");
    await expect(campContrasenya(page)).toHaveValue(CONTRASENYA);
  });

  test("CP-US2-09 · genera i desa el JWT i l'envia a /me", async ({
    page,
    request,
  }) => {
    const dades = await crearUsuari(request);
    let capcaleraAutoritzacio = "";

    page.on("request", (peticio) => {
      if (peticio.url().endsWith(URL_ME) && peticio.method() === "GET") {
        capcaleraAutoritzacio = peticio.headers().authorization ?? "";
      }
    });

    await obrirLogin(page);
    await omplirLogin(page, dades.correu, dades.contrasenya);

    const [respostaLogin] = await enviarLogin(page);

    expect(respostaLogin.status()).toBe(200);
    await expect(page).toHaveURL("/");

    const sessio = await page.evaluate(() =>
      JSON.parse(sessionStorage.getItem("bookit.sessio")),
    );

    expect(sessio.accessToken).toBeTruthy();
    expect(sessio.refreshToken).toBeTruthy();
    expect(capcaleraAutoritzacio).toBe(`Bearer ${sessio.accessToken}`);
    expect(await page.locator("body").textContent()).not.toContain(
      sessio.accessToken,
    );
    expect(await page.locator("body").textContent()).not.toContain(
      sessio.refreshToken,
    );
  });

  test("CP-US2-10 · tancar clicant fora de la capsa", async ({ page }) => {
    await obrirLogin(page);

    await modalLogin(page)
      .getByRole("heading", { name: "Inicia Sessió" })
      .click();
    await expect(modalLogin(page)).toBeVisible();

    const fons = page.locator("main.login-page");
    const requadre = await fons.boundingBox();

    await page.mouse.click(requadre.x + 5, requadre.y + 5);

    await expect(page).toHaveURL("/");
    await expect(modalLogin(page)).toBeHidden();
  });

  test("CP-US2-11 · tancar amb la creu", async ({ page }) => {
    await obrirLogin(page);

    await modalLogin(page)
      .getByRole("button", { name: "Tancar", exact: true })
      .click();

    await expect(page).toHaveURL("/");
    await expect(modalLogin(page)).toBeHidden();
  });

  test("US2-T15 · tancar sessió elimina la sessió i actualitza la capçalera", async ({
    page,
    request,
  }) => {
    const dades = await crearUsuari(request);

    await obrirLogin(page);
    await omplirLogin(page, dades.correu, dades.contrasenya);
    await enviarLogin(page);

    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("button", { name: "Tancar sessió", exact: true }),
    ).toBeVisible();

    await page
      .getByRole("button", { name: "Tancar sessió", exact: true })
      .click();

    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("link", { name: "Inicia sessió", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Registra't", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Tancar sessió", exact: true }),
    ).toBeHidden();

    const sessio = await page.evaluate(() =>
      sessionStorage.getItem("bookit.sessio"),
    );
    expect(sessio).toBeNull();
  });
});
