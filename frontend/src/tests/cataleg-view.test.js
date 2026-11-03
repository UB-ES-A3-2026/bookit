import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import api from "../services/api.js";
import { useSessioStore } from "../stores/sessio.js";
import { nomesBiblioteques } from "../router/index.js";
import CatalegView from "../views/CatalegView.vue";

vi.mock("../services/api.js", () => ({
  default: {
    get: vi.fn(),
  },
}));

const llibres = [
  {
    id: 7,
    titol: "Mecanoscrit del segon origen",
    autor: "Manuel de Pedrolo",
    isbn: "9788466421126",
    portada: "https://example.com/portades/mecanoscrit.jpg",
    exemplars: 3,
  },
  {
    id: 9,
    titol: "Solitud",
    autor: "Víctor Català",
    isbn: "9788475882574",
    portada: "",
    exemplars: 1,
  },
];

let app;

// Deixa que s'acabin la petició simulada i el renderitzat que la segueix.
const esperaRenderitzat = () => new Promise((resolve) => setTimeout(resolve));

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p>Inici</p>" } },
      { path: "/cataleg", name: "cataleg", component: CatalegView },
      { path: "/cataleg/afegir", name: "cataleg-afegir", component: { template: "<p>Afegir</p>" } },
    ],
  });
  router.push("/cataleg");
  await router.isReady();

  const element = document.createElement("div");
  document.body.appendChild(element);
  app = createApp(CatalegView);
  app.use(router);
  app.mount(element);
  await esperaRenderitzat();
  return { element, router };
}

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("El meu catàleg", () => {
  it("demana el catàleg de la biblioteca a l'API", async () => {
    api.get.mockResolvedValue({ data: llibres });
    await renderitza();

    expect(api.get).toHaveBeenCalledWith("/cataleg/biblioteca/llibres/");
  });

  it("mostra cada llibre amb el seu nombre d'exemplars", async () => {
    api.get.mockResolvedValue({ data: llibres });
    const { element } = await renderitza();

    const files = element.querySelectorAll(".llibre");
    expect(files).toHaveLength(2);
    expect(files[0].textContent).toContain("Mecanoscrit del segon origen");
    expect(files[0].textContent).toContain("Manuel de Pedrolo");
    expect(files[0].textContent).toContain("3 exemplars");
    expect(files[1].textContent).toContain("Solitud");
    expect(files[1].textContent).toContain("1 exemplar");
  });

  it("mostra la portada i, si no n'hi ha, la inicial del títol", async () => {
    api.get.mockResolvedValue({ data: llibres });
    const { element } = await renderitza();

    const files = element.querySelectorAll(".llibre");
    expect(files[0].querySelector("img").getAttribute("src")).toBe(llibres[0].portada);
    expect(files[1].querySelector("img")).toBeNull();
    expect(files[1].querySelector(".portada-buida").textContent.trim()).toBe("S");
  });

  it("mostra un missatge mentre carrega", async () => {
    api.get.mockReturnValue(new Promise(() => {}));
    const { element } = await renderitza();

    expect(element.querySelector('[role="status"]').textContent).toContain(
      "Carregant el catàleg",
    );
  });

  it("avisa quan el catàleg és buit", async () => {
    api.get.mockResolvedValue({ data: [] });
    const { element } = await renderitza();

    expect(element.textContent).toContain("Encara no tens cap llibre al catàleg.");
    expect(element.querySelector(".llista-llibres")).toBeNull();
  });

  it("mostra un error si no es pot carregar i permet tornar-ho a provar", async () => {
    api.get.mockRejectedValueOnce({ response: { status: 500 } });
    const { element } = await renderitza();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "No s'ha pogut carregar el catàleg.",
    );

    api.get.mockResolvedValueOnce({ data: llibres });
    element.querySelector(".secondary-button").click();
    await esperaRenderitzat();

    expect(api.get).toHaveBeenCalledTimes(2);
    expect(element.querySelector('[role="alert"]')).toBeNull();
    expect(element.querySelectorAll(".llibre")).toHaveLength(2);
  });

  it("mostra l'error quan no hi ha connexió amb el servidor", async () => {
    api.get.mockRejectedValue(new Error("Network Error"));
    const { element } = await renderitza();

    expect(element.querySelector('[role="alert"]')).not.toBeNull();
  });

  it("torna a l'inici si l'usuari no és una biblioteca", async () => {
    api.get.mockRejectedValue({ response: { status: 403 } });
    const { element, router } = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
    expect(element.querySelector('[role="alert"]')).toBeNull();
  });
});

describe("accés a la ruta del catàleg", () => {
  function sessioAmbRol(rol) {
    setActivePinia(createPinia());
    const sessio = useSessioStore();
    if (rol) {
      sessio.iniciarSessio({ accessToken: "token-de-prova", rol });
    }
  }

  it("deixa entrar una biblioteca", () => {
    sessioAmbRol("biblioteca");
    expect(nomesBiblioteques()).toBe(true);
  });

  it("demana iniciar sessió si no n'hi ha cap", () => {
    sessioAmbRol(null);
    expect(nomesBiblioteques()).toEqual({ name: "inici-sessio" });
  });

  it("torna a l'inici si l'usuari té un altre rol", () => {
    sessioAmbRol("usuari");
    expect(nomesBiblioteques()).toEqual({ name: "home" });

    sessioAmbRol("repartidor");
    expect(nomesBiblioteques()).toEqual({ name: "home" });
  });
});
