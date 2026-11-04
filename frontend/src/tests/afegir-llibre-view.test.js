import { createApp, nextTick } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import api from "../services/api.js";
import { useSessioStore } from "../stores/sessio.js";
import AfegirLlibreView from "../views/AfegirLlibreView.vue";

vi.mock("../services/api.js", () => ({
  default: {
    post: vi.fn(),
  },
}));

const CAMPS_OBLIGATORIS = "Omple tots els camps obligatoris per continuar";

const dadesValides = {
  titol: "Mecanoscrit del segon origen",
  autor: "Manuel de Pedrolo",
  isbn: "978-84-664-2112-6",
  exemplars: "3",
  portada: "https://example.com/portades/mecanoscrit.jpg",
};

let app;
let router;

// Deixa que s'acabin la petició simulada i el renderitzat que la segueix.
const esperaRenderitzat = () => new Promise((resolve) => setTimeout(resolve));

async function renderitza() {
  const pinia = createPinia();
  setActivePinia(pinia);
  useSessioStore().iniciarSessio({
    accessToken: "token-de-prova",
    rol: "biblioteca",
    usuari: { nom: "Biblioteca Montbau" },
  });

  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p>Inici</p>" } },
      { path: "/cataleg", name: "cataleg", component: { template: "<p>Catàleg</p>" } },
      { path: "/cataleg/afegir", name: "cataleg-afegir", component: AfegirLlibreView },
    ],
  });
  router.push("/cataleg/afegir");
  await router.isReady();

  const element = document.createElement("div");
  document.body.appendChild(element);
  app = createApp(AfegirLlibreView);
  app.use(pinia);
  app.use(router);
  app.mount(element);
  return element;
}

function escriu(element, camp, valor) {
  const input = element.querySelector(`#${camp}`);
  input.value = valor;
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function omple(element, dades) {
  Object.entries(dades).forEach(([camp, valor]) => escriu(element, camp, valor));
}

async function envia(element) {
  element.querySelector("form").dispatchEvent(new Event("submit"));
  await esperaRenderitzat();
}

const errorGeneral = (element) => element.querySelector('[role="alert"]')?.textContent.trim();
const errorDe = (element, camp) => element.querySelector(`#${camp}-error`).textContent.trim();
const marcat = (element, camp) => element.querySelector(`#${camp}`).getAttribute("aria-invalid");

beforeEach(() => {
  api.post.mockResolvedValue({ status: 201, data: { id: 7 } });
});

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("formulari per afegir un llibre", () => {
  it("mostra la biblioteca que ha iniciat sessió", async () => {
    const element = await renderitza();

    expect(element.textContent).toContain("Biblioteca Montbau");
  });

  it("envia les dades netes a l'API i torna al catàleg", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, titol: "  Mecanoscrit del segon origen  " });

    await envia(element);

    expect(api.post).toHaveBeenCalledWith("/cataleg/biblioteca/llibres/", {
      titol: "Mecanoscrit del segon origen",
      autor: "Manuel de Pedrolo",
      isbn: "978-84-664-2112-6",
      exemplars: 3,
      portada: "https://example.com/portades/mecanoscrit.jpg",
    });
    expect(router.currentRoute.value.name).toBe("cataleg");
  });

  it("es pot afegir un llibre sense portada", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, portada: "" });

    await envia(element);

    expect(api.post).toHaveBeenCalledWith(
      "/cataleg/biblioteca/llibres/",
      expect.objectContaining({ portada: "" }),
    );
  });

  it("amb camps obligatoris buits mostra el missatge i no envia res", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, titol: "   ", exemplars: "" });

    await envia(element);

    expect(errorGeneral(element)).toBe(CAMPS_OBLIGATORIS);
    expect(marcat(element, "titol")).toBe("true");
    expect(marcat(element, "exemplars")).toBe("true");
    expect(marcat(element, "autor")).toBe("false");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("amb un ISBN incorrecte mostra l'error sota el camp", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, isbn: "978-84-664-2112-7" });

    await envia(element);

    expect(errorDe(element, "isbn")).toBe("L'ISBN introduït no és vàlid");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("no accepta menys d'un exemplar", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, exemplars: "0" });

    await envia(element);

    expect(errorDe(element, "exemplars")).toBe("Aquest valor ha de ser més gran o igual a 1.");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("amb un enllaç de portada incorrecte mostra l'error", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, portada: "portada.jpg" });

    await envia(element);

    expect(errorDe(element, "portada")).toBe("Introduïu una URL vàlida.");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("mostra l'error del backend quan el llibre ja és al catàleg", async () => {
    api.post.mockRejectedValue({
      response: {
        status: 400,
        data: { isbn: ["Aquest llibre ja és al teu catàleg, actualitza'n els exemplars"] },
      },
    });
    const element = await renderitza();
    omple(element, dadesValides);

    await envia(element);

    expect(errorDe(element, "isbn")).toBe(
      "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars",
    );
    expect(router.currentRoute.value.name).toBe("cataleg-afegir");
  });

  it("el missatge de camps obligatoris del backend va a dalt del formulari", async () => {
    api.post.mockRejectedValue({
      response: { status: 400, data: { autor: [CAMPS_OBLIGATORIS] } },
    });
    const element = await renderitza();
    omple(element, dadesValides);

    await envia(element);

    expect(errorGeneral(element)).toBe(CAMPS_OBLIGATORIS);
    expect(errorDe(element, "autor")).toBe("");
    expect(marcat(element, "autor")).toBe("true");
  });

  it("si el backend falla, demana tornar-ho a provar més tard", async () => {
    api.post.mockRejectedValue({ response: { status: 500 } });
    const element = await renderitza();
    omple(element, dadesValides);

    await envia(element);

    expect(errorGeneral(element)).toBe(
      "No s'ha pogut afegir el llibre. Torna-ho a provar més tard.",
    );
  });

  it("torna a l'inici si l'usuari no és una biblioteca", async () => {
    api.post.mockRejectedValue({ response: { status: 403 } });
    const element = await renderitza();
    omple(element, dadesValides);

    await envia(element);

    expect(router.currentRoute.value.name).toBe("home");
  });

  it("en tornar a escriure en un camp se n'esborra l'error", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, isbn: "123" });
    await envia(element);
    expect(errorDe(element, "isbn")).not.toBe("");

    escriu(element, "isbn", "9788466421126");
    await nextTick();

    expect(errorDe(element, "isbn")).toBe("");
  });

  it("el botó Netejar buida el formulari i els errors", async () => {
    const element = await renderitza();
    omple(element, { ...dadesValides, isbn: "123" });
    await envia(element);

    element.querySelector(".boto-secundari").click();
    await nextTick();

    expect(element.querySelector("#titol").value).toBe("");
    expect(element.querySelector("#isbn").value).toBe("");
    expect(errorDe(element, "isbn")).toBe("");
  });
});
