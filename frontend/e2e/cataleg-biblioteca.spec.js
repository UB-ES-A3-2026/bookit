import { test, expect } from "@playwright/test";

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const EMAIL = process.env.E2E_BIBLIOTECA_EMAIL;
const PASSWORD = process.env.E2E_BIBLIOTECA_PASSWORD;

const URL_LOGIN = "/api/auth/login/";
const URL_ME = "/api/auth/me/";
const URL_CATALEG = "/api/cataleg/biblioteca/llibres/";
const URL_CERCA = "/cerca";

const MISSATGE_CAMPS_OBLIGATORIS =
  "Omple tots els camps obligatoris per continuar";
const MISSATGE_ISBN_INVALID = "L'ISBN introduït no és vàlid";
const MISSATGE_DUPLICAT =
  "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars";

function identificador() {
  return `${Date.now()}${Math.floor(Math.random() * 1000000)}`;
}

function isbn13Valid() {
  // Els últims dígits de l'identificador canvien a cada crida; els primers (l'hora) no.
  const base = `978${identificador().slice(-9)}`;
  const suma = [...base].reduce(
    (total, xifra, index) => total + Number(xifra) * (index % 2 === 0 ? 1 : 3),
    0,
  );
  const control = (10 - (suma % 10)) % 10;

  return `${base}${control}`;
}

function dadesLlibre(canvis = {}) {
  const id = identificador();

  return {
    titol: `Llibre E2E ${id}`,
    autor: `Autor E2E ${id}`,
    isbn: isbn13Valid(),
    portada: "https://example.com/portada-e2e.jpg",
    exemplars: "3",
    ...canvis,
  };
}

function campsFormulari(page) {
  return {
    titol: page.getByLabel("Títol", { exact: true }),
    autor: page.getByLabel("Autor o autora", { exact: true }),
    isbn: page.getByLabel("ISBN", { exact: true }),
    exemplars: page.getByLabel("Nombre d'exemplars", { exact: true }),
    portada: page.getByLabel(/Enllaç de la portada/),
  };
}

function llistaCataleg(page) {
  return page.getByRole("list", {
    name: "Llibres del catàleg",
  });
}

function llibreCataleg(page, titol) {
  return llistaCataleg(page)
    .getByRole("listitem")
    .filter({
      has: page.getByRole("heading", {
        name: titol,
        exact: true,
      }),
    });
}

function llistaResultats(page) {
  return page.getByRole("list", {
    name: "Resultats de la cerca",
  });
}

function llibreResultat(page, titol) {
  return llistaResultats(page)
    .getByRole("listitem")
    .filter({
      has: page.getByRole("heading", {
        name: titol,
        exact: true,
      }),
    });
}

async function iniciarSessioBiblioteca(page, request, testInfo) {
  if (!EMAIL || !PASSWORD) {
    testInfo.fixme(
      "Cal definir E2E_BIBLIOTECA_EMAIL i E2E_BIBLIOTECA_PASSWORD amb un compte de biblioteca verificat.",
    );
    return null;
  }

  const respostaLogin = await request.post(`${API_URL}${URL_LOGIN}`, {
    data: {
      correu: EMAIL,
      contrasenya: PASSWORD,
    },
  });

  expect(respostaLogin.status()).toBe(200);

  const tokens = await respostaLogin.json();

  const respostaUsuari = await request.get(`${API_URL}${URL_ME}`, {
    headers: {
      Authorization: `Bearer ${tokens.access}`,
    },
  });

  expect(respostaUsuari.status()).toBe(200);

  const usuari = await respostaUsuari.json();
  expect(usuari.rol).toBe("biblioteca");

  await page.addInitScript(
    ({ access, refresh, dadesUsuari }) => {
      sessionStorage.setItem(
        "bookit.sessio",
        JSON.stringify({
          accessToken: access,
          refreshToken: refresh,
          usuari: dadesUsuari,
          rol: dadesUsuari.rol,
        }),
      );
    },
    {
      access: tokens.access,
      refresh: tokens.refresh,
      dadesUsuari: usuari,
    },
  );

  return tokens.access;
}

async function obrirCataleg(page, request, testInfo) {
  const token = await iniciarSessioBiblioteca(page, request, testInfo);

  if (!token) {
    return null;
  }

  await page.goto("/cataleg");

  await expect(
    page.getByRole("heading", { name: "El meu catàleg" }),
  ).toBeVisible();

  return token;
}

async function omplirAlta(page, dades) {
  const camps = campsFormulari(page);

  await camps.titol.fill(dades.titol);
  await camps.autor.fill(dades.autor);
  await camps.isbn.fill(dades.isbn);
  await camps.exemplars.fill(String(dades.exemplars));
  await camps.portada.fill(dades.portada);
}

async function afegirPerInterficie(page, dades) {
  await page.goto("/cataleg/afegir");

  await expect(
    page.getByRole("heading", { name: "Afegir un llibre" }),
  ).toBeVisible();

  await omplirAlta(page, dades);

  await page
    .getByRole("button", { name: "Afegir al catàleg", exact: false })
    .click();

  await expect(page).toHaveURL("/cataleg");
  await expect(llibreCataleg(page, dades.titol)).toHaveCount(1);
}

async function idDelLlibre(request, token, titol) {
  const resposta = await request.get(`${API_URL}${URL_CATALEG}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  expect(resposta.status()).toBe(200);

  const llibres = await resposta.json();
  return llibres.find((llibre) => llibre.titol === titol)?.id;
}

async function eliminarLlibre(request, token, id) {
  if (!id) {
    return;
  }

  const resposta = await request.delete(`${API_URL}${URL_CATALEG}${id}/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  expect([204, 404]).toContain(resposta.status());
}

async function netejarLlibre(request, token, titol) {
  if (!token) {
    return;
  }

  const id = await idDelLlibre(request, token, titol);
  await eliminarLlibre(request, token, id);
}

test.describe("catàleg de biblioteca (US17-T13)", () => {
  test("CP-US17-01 · afegir un llibre nou amb totes les dades", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      const llibre = llibreCataleg(page, dades.titol);

      await expect(llibre).toContainText(dades.autor);
      await expect(llibre).toContainText(`ISBN ${dades.isbn}`);
      await expect(llibre).toContainText("3 exemplars");
      await expect(
        llibre.getByRole("img", {
          name: `Portada de ${dades.titol}`,
        }),
      ).toHaveAttribute("src", dades.portada);
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  for (const [camp, numero] of [
    ["titol", "02"],
    ["autor", "03"],
    ["isbn", "04"],
    ["exemplars", "05"],
  ]) {
    test(`CP-US17-${numero} · camp ${camp} buit`, async ({
      page,
      request,
    }, testInfo) => {
      const dades = dadesLlibre({ [camp]: "" });
      const token = await obrirCataleg(page, request, testInfo);

      if (!token) {
        return;
      }

      await page.goto("/cataleg/afegir");
      await omplirAlta(page, dades);

      await page
        .getByRole("button", { name: "Afegir al catàleg", exact: false })
        .click();

      await expect(page.getByRole("alert")).toHaveText(
        MISSATGE_CAMPS_OBLIGATORIS,
      );
      await expect(page).toHaveURL("/cataleg/afegir");
    });
  }

  test("CP-US17-06 · tots els camps obligatoris buits", async ({
    page,
    request,
  }, testInfo) => {
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    await page.goto("/cataleg/afegir");

    await page
      .getByRole("button", { name: "Afegir al catàleg", exact: false })
      .click();

    await expect(page.getByRole("alert")).toHaveText(
      MISSATGE_CAMPS_OBLIGATORIS,
    );
    await expect(page).toHaveURL("/cataleg/afegir");
  });

  test("CP-US17-07 · ISBN amb format invàlid", async ({
    page,
    request,
  }, testInfo) => {
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    const dades = dadesLlibre({
      isbn: "123",
    });

    await page.goto("/cataleg/afegir");
    await omplirAlta(page, dades);

    await page
      .getByRole("button", { name: "Afegir al catàleg", exact: false })
      .click();

    await expect(page.getByText(MISSATGE_ISBN_INVALID, { exact: true })).toBeVisible();
    await expect(page).toHaveURL("/cataleg/afegir");
  });

  test("CP-US17-08 · ISBN nou vàlid", async ({ page, request }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);
      await expect(llibreCataleg(page, dades.titol)).toHaveCount(1);
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-09 · ISBN duplicat", async ({ page, request }, testInfo) => {
    const existent = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, existent);

      const duplicat = dadesLlibre({
        isbn: existent.isbn,
      });

      await page.goto("/cataleg/afegir");
      await omplirAlta(page, duplicat);

      await page
        .getByRole("button", { name: "Afegir al catàleg", exact: false })
        .click();

      await expect(page).toHaveURL("/cataleg/afegir");
      // El missatge de duplicat surt sota el camp ISBN (docs/api-cataleg.md).
      await expect(page.getByText(MISSATGE_DUPLICAT, { exact: true })).toBeVisible();
    } finally {
      await netejarLlibre(request, token, existent.titol);
    }
  });

  test("CP-US17-10 · editar les dades d'un llibre", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      const titolEditat = `${dades.titol} editat`;
      const autorEditat = `${dades.autor} editat`;
      const llibre = llibreCataleg(page, dades.titol);

      await llibre.getByRole("button", { name: "Editar" }).click();

      await page.getByLabel("Títol", { exact: true }).fill(titolEditat);
      await page.getByLabel("Autor", { exact: true }).fill(autorEditat);
      await page
        .getByLabel("Portada (URL)", { exact: true })
        .fill("https://example.com/portada-editada.jpg");

      // En editar, el títol del llibre es substitueix pel formulari, així que el
      // botó es busca a la llista i no dins de la fila filtrada pel títol.
      await llistaCataleg(page).getByRole("button", { name: "Desar dades" }).click();

      const editat = llibreCataleg(page, titolEditat);

      await expect(editat).toContainText(autorEditat);
      await expect(
        editat.getByRole("img", {
          name: `Portada de ${titolEditat}`,
        }),
      ).toHaveAttribute("src", "https://example.com/portada-editada.jpg");
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-11 · modificar el nombre d'exemplars", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      const llibre = llibreCataleg(page, dades.titol);

      await page
        .getByLabel(`Exemplars de ${dades.titol}`, { exact: true })
        .fill("0");

      await llibre.getByRole("button", { name: "Actualitzar" }).click();

      await expect(llibre).toContainText("0 exemplars");
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-12 · retirar un llibre del catàleg", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      const llibre = llibreCataleg(page, dades.titol);

      page.once("dialog", (dialog) => dialog.accept());
      await llibre.getByRole("button", { name: "Retirar" }).click();

      await expect(llibreCataleg(page, dades.titol)).toHaveCount(0);
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-13 · el llibre afegit apareix a la cerca", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);
      await page.goto(`${URL_CERCA}?q=${encodeURIComponent(dades.titol)}`);

      const resultat = llibreResultat(page, dades.titol);

      await expect(resultat).toHaveCount(1);
      await expect(resultat).toContainText(dades.autor);
      await expect(resultat).toContainText("Disponible");
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-14 · les dades editades apareixen a la cerca", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      const titolEditat = `${dades.titol} editat`;
      const autorEditat = `${dades.autor} editat`;
      const llibre = llibreCataleg(page, dades.titol);

      await llibre.getByRole("button", { name: "Editar" }).click();
      await page.getByLabel("Títol", { exact: true }).fill(titolEditat);
      await page.getByLabel("Autor", { exact: true }).fill(autorEditat);
      await page.getByRole("button", { name: "Desar dades" }).click();

      await page.goto(`${URL_CERCA}?q=${encodeURIComponent(titolEditat)}`);

      const resultat = llibreResultat(page, titolEditat);

      await expect(resultat).toHaveCount(1);
      await expect(resultat).toContainText(autorEditat);
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test("CP-US17-15 · la disponibilitat reflecteix el canvi d'exemplars", async ({
    page,
    request,
  }, testInfo) => {
    const dades = dadesLlibre();
    const token = await obrirCataleg(page, request, testInfo);

    if (!token) {
      return;
    }

    try {
      await afegirPerInterficie(page, dades);

      await page.goto(`${URL_CERCA}?q=${encodeURIComponent(dades.titol)}`);

      await expect(llibreResultat(page, dades.titol)).toContainText(
        "Disponible",
      );

      await page.goto("/cataleg");

      const llibre = llibreCataleg(page, dades.titol);

      await page
        .getByLabel(`Exemplars de ${dades.titol}`, { exact: true })
        .fill("0");

      await llibre.getByRole("button", { name: "Actualitzar" }).click();

      await page.goto(`${URL_CERCA}?q=${encodeURIComponent(dades.titol)}`);

      await expect(llibreResultat(page, dades.titol)).toContainText(
        "No disponible",
      );
    } finally {
      await netejarLlibre(request, token, dades.titol);
    }
  });

  test.fixme("CP-US17-16 · el llibre retirat desapareix de la cerca", async () => {
    // El backend actual manté el llibre a la taula Llibre després de retirar-lo
    // i la cerca el continua mostrant com a «No disponible».
    // Cal confirmar aquest comportament amb el Product Owner.
  });
});
