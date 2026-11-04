import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useSessioStore } from "../stores/sessio.js";
import { nomesBiblioteques } from "../router/index.js";
import CatalegView from "../views/CatalegView.vue";

const serveisCataleg = vi.hoisted(() => ({
  llistaCataleg: vi.fn(),
  editaLlibre: vi.fn(),
  actualitzaExemplars: vi.fn(),
  retiraLlibre: vi.fn(),
}));

vi.mock("../services/cataleg.js", () => ({
  llistaCataleg: serveisCataleg.llistaCataleg,
  editaLlibre: serveisCataleg.editaLlibre,
  actualitzaExemplars: serveisCataleg.actualitzaExemplars,
  retiraLlibre: serveisCataleg.retiraLlibre,
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
  app.use(createPinia());
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
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    await renderitza();

    expect(serveisCataleg.llistaCataleg).toHaveBeenCalledOnce();
  });

  it("mostra cada llibre amb el seu nombre d'exemplars", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
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
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    const { element } = await renderitza();

    const files = element.querySelectorAll(".llibre");
    expect(files[0].querySelector("img").getAttribute("src")).toBe(llibres[0].portada);
    expect(files[1].querySelector("img")).toBeNull();
    expect(files[1].querySelector(".portada-buida").textContent.trim()).toBe("S");
  });

  it("mostra un missatge mentre carrega", async () => {
    serveisCataleg.llistaCataleg.mockReturnValue(new Promise(() => {}));
    const { element } = await renderitza();

    expect(element.querySelector('[role="status"]').textContent).toContain(
      "Carregant el catàleg",
    );
  });

  it("avisa quan el catàleg és buit", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue([]);
    const { element } = await renderitza();

    expect(element.textContent).toContain("Encara no tens cap llibre al catàleg.");
    expect(element.querySelector(".llista-llibres")).toBeNull();
  });

  it("mostra un error si no es pot carregar i permet tornar-ho a provar", async () => {
    serveisCataleg.llistaCataleg.mockRejectedValueOnce({ response: { status: 500 } });
    const { element } = await renderitza();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "No s'ha pogut carregar el catàleg.",
    );

    serveisCataleg.llistaCataleg.mockResolvedValueOnce(llibres);
    element.querySelector(".secondary-button").click();
    await esperaRenderitzat();

    expect(serveisCataleg.llistaCataleg).toHaveBeenCalledTimes(2);
    expect(element.querySelector('[role="alert"]')).toBeNull();
    expect(element.querySelectorAll(".llibre")).toHaveLength(2);
  });

  it("mostra l'error quan no hi ha connexió amb el servidor", async () => {
    serveisCataleg.llistaCataleg.mockRejectedValue(new Error("Network Error"));
    const { element } = await renderitza();

    expect(element.querySelector('[role="alert"]')).not.toBeNull();
  });

  it("torna a l'inici si l'usuari no és una biblioteca", async () => {
    serveisCataleg.llistaCataleg.mockRejectedValue({ response: { status: 403 } });
    const { element, router } = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
    expect(element.querySelector('[role="alert"]')).toBeNull();
  });

  it("permet editar les dades d'un llibre", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    serveisCataleg.editaLlibre.mockResolvedValue({
      ...llibres[0],
      titol: "Mecanoscrit revisat",
      autor: "Autor nou",
      portada: "https://example.com/nova.jpg",
    });
    const { element } = await renderitza();

    element.querySelector(".llibre button").click();
    await esperaRenderitzat();
    const inputs = element.querySelectorAll(".formulari-edicio input");
    inputs[0].value = "Mecanoscrit revisat";
    inputs[0].dispatchEvent(new Event("input", { bubbles: true }));
    inputs[1].value = "Autor nou";
    inputs[1].dispatchEvent(new Event("input", { bubbles: true }));
    element.querySelector(".formulari-edicio button").click();
    await esperaRenderitzat();

    expect(serveisCataleg.editaLlibre).toHaveBeenCalledWith(7, {
      titol: "Mecanoscrit revisat",
      autor: "Autor nou",
      portada: "https://example.com/portades/mecanoscrit.jpg",
    });
    expect(element.textContent).toContain("Mecanoscrit revisat");
    expect(element.querySelector(".formulari-edicio")).toBeNull();
  });

  it("valida els camps obligatoris abans d'editar", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    const { element } = await renderitza();

    element.querySelector(".llibre button").click();
    await esperaRenderitzat();
    const titol = element.querySelector(".formulari-edicio input");
    titol.value = "   ";
    titol.dispatchEvent(new Event("input", { bubbles: true }));
    element.querySelector(".formulari-edicio button").click();
    await esperaRenderitzat();

    expect(serveisCataleg.editaLlibre).not.toHaveBeenCalled();
    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "El títol i l'autor són obligatoris",
    );
  });

  it("actualitza els exemplars i permet establir-los a zero", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    serveisCataleg.actualitzaExemplars.mockResolvedValue({
      ...llibres[0],
      exemplars: 0,
    });
    const { element } = await renderitza();

    const fila = element.querySelector(".llibre");
    const input = fila.querySelector(".camp-exemplars input");
    input.value = "0";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    fila.querySelector(".camp-exemplars button").click();
    await esperaRenderitzat();

    expect(serveisCataleg.actualitzaExemplars).toHaveBeenCalledWith(7, 0);
    expect(fila.textContent).toContain("0 exemplars");
  });

  it("retira un llibre només després de confirmar", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    serveisCataleg.retiraLlibre.mockResolvedValue();
    vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValueOnce(true);
    const { element } = await renderitza();

    const retirar = element.querySelectorAll(".danger-button")[0];
    retirar.click();
    await esperaRenderitzat();
    expect(serveisCataleg.retiraLlibre).not.toHaveBeenCalled();
    expect(element.querySelectorAll(".llibre")).toHaveLength(2);

    retirar.click();
    await esperaRenderitzat();
    expect(serveisCataleg.retiraLlibre).toHaveBeenCalledWith(7);
    expect(element.querySelectorAll(".llibre")).toHaveLength(1);
    expect(element.textContent).toContain("Solitud");
  });

  it("mostra errors de les accions sense perdre la llista", async () => {
    serveisCataleg.llistaCataleg.mockResolvedValue(llibres);
    serveisCataleg.editaLlibre.mockRejectedValue(new Error("Network Error"));
    const { element } = await renderitza();

    element.querySelector(".llibre button").click();
    await esperaRenderitzat();
    element.querySelector(".formulari-edicio button").click();
    await esperaRenderitzat();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "No s'han pogut desar les dades",
    );
    expect(element.querySelectorAll(".llibre")).toHaveLength(2);
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
