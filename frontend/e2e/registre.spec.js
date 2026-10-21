import { test, expect } from "@playwright/test";

// Tests E2E del registre d'usuari (US1-T13).
// Cada test correspon a un cas de docs/casos-prova-us1.md. Els casos de l'API (CP-US1-17 i 18) ja els cobreixen els
// tests del backend (US1-T6), i el CP-US1-14 (espais), el 19 (teclat) i el 20 (doble clic) es proven a mà a la T14.
// El CP-US1-16 no hi és perquè el disseny no té el camp per repetir la contrasenya.
//
// Els tests que envien el formulari necessiten el backend aixecat amb Docker (`docker compose up -d --build --wait`)
// i CORS configurat (US1-T17). Els grups marcats amb test.fixme depenen de tasques de frontend que encara no són a
// aquesta branca: cal treure el fixme del grup quan hi arribin.

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const URL_REGISTRE_API = "/api/auth/register/";

const CAMPS = {
  correu: "Correu electrònic",
  nom: "Nom complet",
  adreca: "Adreça física",
  num_carnet: "Número de carnet de biblioteca",
  contrasenya: "Contrasenya",
};

const titol = (page) => page.getByRole("heading", { name: "Crear un compte" });
const camp = (page, nom) => page.getByLabel(CAMPS[nom], { exact: true });
const tipusCompte = (page, nom) => page.getByRole("button", { name: nom, exact: true });
const termes = (page) => page.getByRole("checkbox", { name: /Accepto els termes d'ús/ });
const botoEnviar = (page) => page.getByRole("button", { name: "Completar Registre" });

// Expressió que troba el text dins de la descripció accessible del camp (l'ajuda i el missatge d'error).
const conte = (text) => new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

// Correu i carnet únics a cada test: la base de dades local es conserva entre execucions.
function dadesNoves(canvis = {}) {
  const id = String(Math.floor(Math.random() * 1e10)).padStart(10, "0");
  return {
    correu: `e2e.${id}@example.com`,
    nom: "Anna Puig",
    adreca: "C/ Major 1, 08001 Barcelona",
    num_carnet: id,
    contrasenya: "Llibres-de-tardor-24",
    ...canvis,
  };
}

// Crea un compte directament amb l'API, per als casos que en necessiten un de ja registrat. Cada test en crea un de
// propi: si diversos workers creen el mateix compte alhora, el backend respon 500 (vegeu docs/prova-manual-us1.md).
async function crearCompte(request) {
  const dades = dadesNoves();
  const resposta = await request.post(`${API_URL}${URL_REGISTRE_API}`, { data: dades });
  expect(resposta.status()).toBe(201);
  return dades;
}

async function obrirCaixa(page) {
  await page.goto("/");
  await page.getByRole("link", { name: "Registra't" }).click();
  await expect(page).toHaveURL("/registre");
  await expect(titol(page)).toBeVisible();
}

async function omplir(page, dades) {
  for (const nom of Object.keys(CAMPS)) {
    await camp(page, nom).fill(dades[nom]);
  }
  await termes(page).check();
}

// Envia el formulari i retorna la resposta del POST al backend.
async function enviar(page) {
  const resposta = page.waitForResponse(
    (r) => r.url().endsWith(URL_REGISTRE_API) && r.request().method() === "POST",
  );
  await botoEnviar(page).click();
  return resposta;
}

// Guarda les peticions al registre del backend, per comprovar que no se n'envia cap.
function peticionsDeRegistre(page) {
  const peticions = [];
  page.on("request", (peticio) => {
    if (peticio.url().endsWith(URL_REGISTRE_API) && peticio.method() === "POST") peticions.push(peticio);
  });
  return peticions;
}

async function esperaQueEsMantinguiOberta(page) {
  await expect(page).toHaveURL("/registre");
  await expect(titol(page)).toBeVisible();
}

test.describe("caixa de registre (US1-T7)", () => {
  test("CP-US1-01 · la caixa mostra els camps de CA1 i Lector triat", async ({ page }) => {
    await obrirCaixa(page);

    for (const nom of Object.keys(CAMPS)) {
      await expect(camp(page, nom)).toBeVisible();
    }
    await expect(tipusCompte(page, "Lector")).toHaveAttribute("aria-pressed", "true");
    await expect(tipusCompte(page, "Repartidor")).toHaveAttribute("aria-pressed", "false");
    await expect(tipusCompte(page, "Biblioteca")).toHaveAttribute("aria-pressed", "false");
    await expect(botoEnviar(page)).toBeVisible();
  });

  test("CP-US1-09 · el botó Tancar tanca la caixa", async ({ page }) => {
    await obrirCaixa(page);

    await page.getByRole("button", { name: "Tancar" }).click();

    await expect(page).toHaveURL("/");
    await expect(titol(page)).toBeHidden();
  });

  test.describe("en mòbil", () => {
    test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

    test("CP-US1-02 · tots els elements de la caixa es veuen sencers", async ({ page }) => {
      await obrirCaixa(page);

      const elements = [
        tipusCompte(page, "Lector"),
        tipusCompte(page, "Repartidor"),
        tipusCompte(page, "Biblioteca"),
        ...Object.keys(CAMPS).map((nom) => camp(page, nom)),
        termes(page),
        botoEnviar(page),
      ];
      for (const element of elements) {
        await element.scrollIntoViewIfNeeded();
        await expect(element).toBeInViewport({ ratio: 1 });
      }
      const ampladaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(ampladaPagina).toBeLessThanOrEqual(375);
    });
  });
});

test.describe("registre amb el backend (US1-T9 i US1-T10)", () => {
  test.fixme(true, "Falta connectar el formulari amb l'API (US1-T9) i redirigir a l'inici (US1-T10).");

  test("CP-US1-01 · registre correcte com a Lector", async ({ page }) => {
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (missatge) => {
      if (missatge.type() === "error") errors.push(missatge.text());
    });
    const dades = dadesNoves();
    await obrirCaixa(page);
    await omplir(page, dades);

    const resposta = await enviar(page);

    expect(resposta.status()).toBe(201);
    expect(await resposta.json()).toMatchObject({
      nom: dades.nom,
      correu: dades.correu,
      adreca: dades.adreca,
      num_carnet: dades.num_carnet,
      rol: "usuari",
    });
    await expect(page).toHaveURL("/");
    await expect(titol(page)).toBeHidden();
    expect(errors).toEqual([]);
  });

  test.describe("en mòbil", () => {
    test.use({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });

    test("CP-US1-02 · registre correcte en mòbil", async ({ page }) => {
      await obrirCaixa(page);
      await omplir(page, dadesNoves());

      const resposta = page.waitForResponse(
        (r) => r.url().endsWith(URL_REGISTRE_API) && r.request().method() === "POST",
      );
      await botoEnviar(page).tap();

      expect((await resposta).status()).toBe(201);
      await expect(page).toHaveURL("/");
    });
  });

  test("CP-US1-03 · correu ja registrat", async ({ page, request }) => {
    const existent = await crearCompte(request);
    await obrirCaixa(page);
    await omplir(page, dadesNoves({ correu: existent.correu }));

    const resposta = await enviar(page);

    expect(resposta.status()).toBe(400);
    await esperaQueEsMantinguiOberta(page);
    await expect(camp(page, "correu")).toHaveAccessibleDescription("Aquest correu electrònic ja està registrat");
  });

  test("CP-US1-04 · correu ja registrat amb majúscules diferents", async ({ page, request }) => {
    const existent = await crearCompte(request);
    await obrirCaixa(page);
    await omplir(page, dadesNoves({ correu: existent.correu.toUpperCase() }));

    const resposta = await enviar(page);

    expect(resposta.status()).toBe(400);
    await esperaQueEsMantinguiOberta(page);
    await expect(camp(page, "correu")).toHaveAccessibleDescription("Aquest correu electrònic ja està registrat");
  });

  test("CP-US1-05 · carnet ja registrat", async ({ page, request }) => {
    const existent = await crearCompte(request);
    await obrirCaixa(page);
    await omplir(page, dadesNoves({ num_carnet: existent.num_carnet }));

    const resposta = await enviar(page);

    expect(resposta.status()).toBe(400);
    await esperaQueEsMantinguiOberta(page);
    await expect(camp(page, "num_carnet")).toHaveAccessibleDescription(conte("Aquest usuari ja està registrat"));
  });

  test("CP-US1-06 · correu i carnet ja registrats alhora", async ({ page, request }) => {
    const existent = await crearCompte(request);
    await obrirCaixa(page);
    await omplir(page, dadesNoves({ correu: existent.correu, num_carnet: existent.num_carnet }));

    await enviar(page);

    await esperaQueEsMantinguiOberta(page);
    await expect(camp(page, "correu")).toHaveAccessibleDescription("Aquest correu electrònic ja està registrat");
    await expect(camp(page, "num_carnet")).toHaveAccessibleDescription(conte("Aquest usuari ja està registrat"));
  });

  test("CP-US1-07 · format de carnet incorrecte", async ({ page }) => {
    await obrirCaixa(page);

    for (const carnet of ["123456789", "12345678901", "123456789A", "BIB-12345678", " 1234567890"]) {
      await omplir(page, dadesNoves({ num_carnet: carnet }));

      const resposta = await enviar(page);

      expect(resposta.status(), `carnet "${carnet}"`).toBe(400);
      await esperaQueEsMantinguiOberta(page);
      await expect(camp(page, "num_carnet")).toHaveAccessibleDescription(
        conte("El format d'aquest carnet no és vàlid"),
      );
    }
  });

  test("CP-US1-13 · correu amb format incorrecte", async ({ page }) => {
    await obrirCaixa(page);

    for (const correu of ["anna.example.com", "anna@", "anna@example", "anna puig@example.com"]) {
      await omplir(page, dadesNoves({ correu }));

      await botoEnviar(page).click();

      await esperaQueEsMantinguiOberta(page);
      await expect(camp(page, "correu"), `correu "${correu}"`).not.toHaveAccessibleDescription("");
    }
  });

  // Els intents 1 i 3 fallen amb el backend actual: el missatge de contrasenya curta arriba en anglès i el validador
  // de semblança amb el correu no s'aplica (vegeu les observacions de docs/casos-prova-us1.md).
  test("CP-US1-15 · contrasenya rebutjada pel backend", async ({ page }) => {
    await obrirCaixa(page);
    const intents = [
      dadesNoves({ contrasenya: "curta1" }),
      dadesNoves({ contrasenya: "12345678" }),
      dadesNoves({ correu: `jordi.vila.${Date.now()}@example.com`, contrasenya: "jordi.vila.example" }),
    ];

    for (const dades of intents) {
      await omplir(page, dades);

      const resposta = await enviar(page);

      expect(resposta.status(), `contrasenya "${dades.contrasenya}"`).toBe(400);
      await esperaQueEsMantinguiOberta(page);
      await expect(camp(page, "contrasenya")).not.toHaveAccessibleDescription("");
      await expect(camp(page, "contrasenya")).not.toHaveAccessibleDescription(/password/i);
    }
  });
});

test.describe("camps obligatoris (US1-T8 o US1-T9)", () => {
  test.fixme(true, "Falta la validació al client (US1-T8) o la connexió amb l'API (US1-T9).");

  test("CP-US1-08 · enviar el formulari amb camps buits", async ({ page }) => {
    await obrirCaixa(page);

    await botoEnviar(page).click();

    await esperaQueEsMantinguiOberta(page);
    for (const nom of Object.keys(CAMPS)) {
      await expect(camp(page, nom), CAMPS[nom]).toHaveAccessibleDescription(conte("obligatori"));
    }

    await omplir(page, { ...dadesNoves(), adreca: "" });
    await botoEnviar(page).click();

    await esperaQueEsMantinguiOberta(page);
    await expect(camp(page, "adreca")).toHaveAccessibleDescription(conte("obligatori"));
    for (const nom of ["correu", "nom", "contrasenya"]) {
      await expect(camp(page, nom), CAMPS[nom]).toHaveAccessibleDescription("");
    }
  });
});

test.describe("tipus de compte no disponibles (US1-T11)", () => {
  test.fixme(true, "Falta l'avís \"Funcionalitat no implementada\" (US1-T11 i US1-T18).");

  for (const [cas, tipus] of [
    ["CP-US1-10", "Repartidor"],
    ["CP-US1-11", "Biblioteca"],
  ]) {
    test(`${cas} · tipus de compte "${tipus}"`, async ({ page }) => {
      const peticions = peticionsDeRegistre(page);
      await obrirCaixa(page);

      await tipusCompte(page, tipus).click();

      await expect(page.getByText("Funcionalitat no implementada")).toBeVisible();

      await omplir(page, dadesNoves());
      if (await botoEnviar(page).isEnabled()) {
        await botoEnviar(page).click();
      }

      await expect(page).toHaveURL("/registre");
      expect(peticions).toEqual([]);
    });
  }

  test("CP-US1-12 · tornar a Lector després de l'avís", async ({ page }) => {
    test.fixme(true, "També necessita la connexió amb l'API (US1-T9) i la redirecció (US1-T10).");
    await obrirCaixa(page);
    await tipusCompte(page, "Repartidor").click();
    await expect(page.getByText("Funcionalitat no implementada")).toBeVisible();

    await tipusCompte(page, "Lector").click();

    await expect(page.getByText("Funcionalitat no implementada")).toBeHidden();
    await omplir(page, dadesNoves());
    const resposta = await enviar(page);
    expect(resposta.status()).toBe(201);
    expect((await resposta.json()).rol).toBe("usuari");
    await expect(page).toHaveURL("/");
  });
});

test.describe("clicar fora de la caixa (CA6)", () => {
  test.fixme(true, "Cap tasca de frontend no implementa encara CA6 (vegeu docs/casos-prova-us1.md).");

  test("CP-US1-09 · clicar fora de la caixa la tanca", async ({ page }) => {
    await obrirCaixa(page);
    const caixa = page.getByRole("region", { name: "Crear un compte" });
    const requadre = await caixa.boundingBox();

    // Clic a dins de la caixa, en una zona buida al costat del títol.
    await page.mouse.click(requadre.x + requadre.width - 80, requadre.y + 70);
    await esperaQueEsMantinguiOberta(page);

    // Seleccionar text arrossegant des de dins i deixar anar a fora no l'ha de tancar.
    await camp(page, "nom").fill("Anna Puig");
    const campNom = await camp(page, "nom").boundingBox();
    await page.mouse.move(campNom.x + 5, campNom.y + campNom.height / 2);
    await page.mouse.down();
    await page.mouse.move(requadre.x + requadre.width + 40, campNom.y + campNom.height / 2);
    await page.mouse.up();
    await esperaQueEsMantinguiOberta(page);

    // Clic al fons enfosquit, fora de la caixa.
    await page.mouse.click(Math.max(requadre.x / 2, 5), requadre.y + requadre.height / 2);

    await expect(page).toHaveURL("/");
    await expect(titol(page)).toBeHidden();
  });
});
