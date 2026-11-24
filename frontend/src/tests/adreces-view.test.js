import { createApp, h, nextTick } from "vue";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AdrecesView from "../views/AdrecesView.vue";
import {
  afegeixAdreca,
  editaAdreca,
  llistaAdreces,
  marcaAdrecaPredeterminada,
  suprimeixAdreca,
} from "../services/adreces.js";

vi.mock("../services/adreces.js", () => ({
  afegeixAdreca: vi.fn(),
  editaAdreca: vi.fn(),
  llistaAdreces: vi.fn(),
  marcaAdrecaPredeterminada: vi.fn(),
  suprimeixAdreca: vi.fn(),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const adrecaInicial = {
  id: 1,
  municipi: "Barcelona",
  carrer: "Carrer Major 1",
  pis: "2n A",
  codi_postal: "08001",
  predeterminada: true,
};

const dadesAdreca = {
  municipi: "Girona",
  carrer: "Carrer Nou 5",
  pis: "4t",
  codi_postal: "17001",
};

let app;

function renderitza() {
  const element = document.createElement("div");
  document.body.appendChild(element);
  const pinia = createPinia();
  setActivePinia(pinia);
  app = createApp(AdrecesView);
  app.use(pinia);
  app.component("RouterLink", {
    props: ["to"],
    setup(props, { slots }) {
      return () =>
        h("a", { href: typeof props.to === "string" ? props.to : "#" }, slots.default?.());
    },
  });
  app.mount(element);
  return element;
}

async function esperaActualitzacio() {
  await Promise.resolve();
  await nextTick();
  await Promise.resolve();
  await nextTick();
}

function obreFormulari(element) {
  const botons = [...element.querySelectorAll("button")];
  botons.find((boto) => boto.textContent.includes("Afegir nova adreça")).click();
}

function ompleFormulari(element, dades = dadesAdreca) {
  Object.entries(dades).forEach(([camp, valor]) => {
    const input = element.querySelector(`#adreca-${camp}`);
    input.value = valor;
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  sessionStorage.clear();
  vi.restoreAllMocks();
});

beforeEach(() => {
  setActivePinia(createPinia());
  llistaAdreces.mockResolvedValue([]);
  afegeixAdreca.mockReset();
  editaAdreca.mockReset();
  marcaAdrecaPredeterminada.mockReset();
  suprimeixAdreca.mockReset();
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

describe("pàgina Les meves adreces", () => {
  it("mostra les adreces carregades i marca la predeterminada", async () => {
    llistaAdreces.mockResolvedValue([adrecaInicial]);
    const element = renderitza();
    await esperaActualitzacio();

    expect(element.textContent).toContain("Carrer Major 1");
    expect(element.textContent).toContain("Barcelona");
    expect(element.textContent).toContain("Predeterminada");
    expect(llistaAdreces).toHaveBeenCalledOnce();
  });

  it("valida els camps obligatoris abans d'afegir una adreça", async () => {
    const element = renderitza();
    await esperaActualitzacio();
    obreFormulari(element);
    await nextTick();
    element.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await nextTick();

    expect(element.textContent.match(/Aquest camp és obligatori\./g)).toHaveLength(4);
    expect(afegeixAdreca).not.toHaveBeenCalled();
  });

  it("afegeix una adreça i la incorpora a la llista", async () => {
    const adrecaNova = { id: 2, ...dadesAdreca, predeterminada: false };
    afegeixAdreca.mockResolvedValue(adrecaNova);
    const element = renderitza();
    await esperaActualitzacio();
    obreFormulari(element);
    await nextTick();
    ompleFormulari(element);
    await nextTick();
    element.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await esperaActualitzacio();

    expect(afegeixAdreca).toHaveBeenCalledWith(dadesAdreca);
    expect(element.textContent).toContain("Carrer Nou 5");
    expect(element.textContent).toContain("Girona");
  });

  it("edita una adreça existent", async () => {
    llistaAdreces.mockResolvedValue([adrecaInicial]);
    const adrecaActualitzada = { ...adrecaInicial, ...dadesAdreca };
    editaAdreca.mockResolvedValue(adrecaActualitzada);
    const element = renderitza();
    await esperaActualitzacio();
    element.querySelector('[aria-label="Editar l\'adreça de Carrer Major 1"]').click();
    await nextTick();
    ompleFormulari(element);
    await nextTick();
    element.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await esperaActualitzacio();

    expect(editaAdreca).toHaveBeenCalledWith(adrecaInicial.id, dadesAdreca);
    expect(element.textContent).toContain("Carrer Nou 5");
    expect(element.textContent).not.toContain("Carrer Major 1");
  });

  it("mostra al camp el missatge de validació de zona del backend", async () => {
    afegeixAdreca.mockRejectedValue({
      response: {
        status: 400,
        data: {
          codi_postal: [
            "Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida",
          ],
        },
      },
    });
    const element = renderitza();
    await esperaActualitzacio();
    obreFormulari(element);
    await nextTick();
    ompleFormulari(element);
    await nextTick();
    element.querySelector("form").dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await esperaActualitzacio();

    expect(element.querySelector("#adreca-codi_postal-error").textContent).toContain(
      "Aquesta adreça està fora de la zona de servei",
    );
    expect(element.querySelector(".zone-warning").textContent).toContain(
      "Aquesta adreça està fora de la zona de servei",
    );
  });

  it("marca una adreça com a predeterminada i actualitza la llista", async () => {
    const altraAdreca = {
      ...adrecaInicial,
      id: 2,
      carrer: "Carrer Nou 5",
      predeterminada: false,
    };
    llistaAdreces.mockResolvedValue([adrecaInicial, altraAdreca]);
    marcaAdrecaPredeterminada.mockResolvedValue({
      ...altraAdreca,
      predeterminada: true,
    });
    const element = renderitza();
    await esperaActualitzacio();

    element
      .querySelector('[aria-label="Fer predeterminada l\'adreça de Carrer Nou 5"]')
      .click();
    await esperaActualitzacio();

    expect(marcaAdrecaPredeterminada).toHaveBeenCalledWith(altraAdreca.id);
    expect(element.querySelectorAll(".default-badge")).toHaveLength(1);
    expect(
      element.querySelector('[aria-label="Fer predeterminada l\'adreça de Carrer Major 1"]'),
    ).not.toBeNull();
    expect(
      element.querySelector('[aria-label="Fer predeterminada l\'adreça de Carrer Nou 5"]'),
    ).toBeNull();
  });

  it("mostra el detall del backend si no pot marcar l'adreça predeterminada", async () => {
    const altraAdreca = { ...adrecaInicial, predeterminada: false };
    llistaAdreces.mockResolvedValue([altraAdreca]);
    marcaAdrecaPredeterminada.mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "No s'ha pogut actualitzar l'adreça predeterminada." },
      },
    });
    const element = renderitza();
    await esperaActualitzacio();

    element
      .querySelector('[aria-label="Fer predeterminada l\'adreça de Carrer Major 1"]')
      .click();
    await esperaActualitzacio();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "No s'ha pogut actualitzar l'adreça predeterminada.",
    );
  });

  it("suprimeix una adreça després de confirmar-ho", async () => {
    llistaAdreces.mockResolvedValue([adrecaInicial]);
    const element = renderitza();
    await esperaActualitzacio();
    element.querySelector('[aria-label="Suprimir l\'adreça de Carrer Major 1"]').click();
    await esperaActualitzacio();

    expect(window.confirm).toHaveBeenCalledOnce();
    expect(suprimeixAdreca).toHaveBeenCalledWith(adrecaInicial.id);
    expect(element.textContent).toContain("Encara no tens cap adreça desada.");
  });
});
