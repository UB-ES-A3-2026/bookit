import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ComandaView from "../views/ComandaView.vue";
import { useComandaStore } from "../stores/comanda.js";

const serveis = vi.hoisted(() => ({
  obtenirCostosLliurament: vi.fn(),
  confirmaComanda: vi.fn(),
}));

vi.mock("../services/prestecs.js", () => serveis);

let app;

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/comanda", name: "comanda", component: ComandaView }],
  });
  await router.push("/comanda");
  await router.isReady();

  const pinia = createPinia();
  setActivePinia(pinia);
  app = createApp(ComandaView);
  app.use(pinia);
  app.use(router);

  const element = document.createElement("div");
  document.body.appendChild(element);
  app.mount(element);

  const comanda = useComandaStore(pinia);
  comanda.afegirLlibre({
    id: 7,
    titol: "La plaça del Diamant",
    autor: "Mercè Rodoreda",
    biblioteca: { id: 3, nom: "Biblioteca" },
  });
  await new Promise((resolve) => setTimeout(resolve));
  return element;
}

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
  serveis.obtenirCostosLliurament.mockResolvedValue({
    domicili: "2.50",
    recollida: "0.00",
  });
});

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("tipus de lliurament de la comanda", () => {
  it("mostra els costos i permet triar recollida", async () => {
    const element = await renderitza();

    expect(element.textContent).toContain("2,50 €");
    expect(element.textContent).toContain("0,00 €");

    const recollida = element.querySelector('input[value="recollida"]');
    recollida.click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.querySelector(".camp-adreca")).toBeNull();
  });

  it("envia domicili amb l'adreça i el tipus triat", async () => {
    serveis.confirmaComanda.mockResolvedValue({ id: 12 });
    const element = await renderitza();

    const adreca = element.querySelector(".camp-adreca input");
    adreca.value = "C/ de Provença 123";
    adreca.dispatchEvent(new Event("input", { bubbles: true }));
    element.querySelector(".confirm-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(serveis.confirmaComanda).toHaveBeenCalledWith({
      biblioteca: 3,
      llibres: [7],
      tipus_lliurament: "domicili",
      adreca_lliurament: "C/ de Provença 123",
    });
  });

  it("consulta el cost de lliurament en muntar la pàgina", async () => {
    await renderitza();

    expect(serveis.obtenirCostosLliurament).toHaveBeenCalledOnce();
  });

  it("mostra el cost de domicili i el canvi a 0,00 € amb recollida", async () => {
    const element = await renderitza();

    expect(element.querySelector(".cost-total strong").textContent.trim()).toBe(
      "2,50 €",
    );

    element.querySelector('input[value="recollida"]').click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.querySelector(".cost-total strong").textContent.trim()).toBe(
      "0,00 €",
    );
  });

  it("envia recollida sense adreça i amb cost zero", async () => {
    serveis.confirmaComanda.mockResolvedValue({ id: 12 });
    const element = await renderitza();

    element.querySelector('input[value="recollida"]').click();
    await new Promise((resolve) => setTimeout(resolve));
    element.querySelector(".confirm-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(serveis.confirmaComanda).toHaveBeenCalledWith({
      biblioteca: 3,
      llibres: [7],
      tipus_lliurament: "recollida",
      adreca_lliurament: "",
    });
  });

  it("rebutja domicili sense adreça i no envia la comanda", async () => {
    const element = await renderitza();
    const adreca = element.querySelector(".camp-adreca input");
    adreca.value = "   ";
    adreca.dispatchEvent(new Event("input", { bubbles: true }));

    element.querySelector(".confirm-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(serveis.confirmaComanda).not.toHaveBeenCalled();
    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "Indica l'adreça de lliurament.",
    );
  });

  it("mostra els errors exactes retornats per l'API", async () => {
    serveis.confirmaComanda.mockRejectedValue({
      response: {
        data: {
          tipus_lliurament: [
            "Tria lliurament a domicili o recollida a la biblioteca.",
          ],
        },
      },
    });
    const element = await renderitza();

    const adreca = element.querySelector(".camp-adreca input");
    adreca.value = "C/ de Provença 123";
    adreca.dispatchEvent(new Event("input", { bubbles: true }));
    element.querySelector(".confirm-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.querySelector('[role="alert"]').textContent).toBe(
      "Tria lliurament a domicili o recollida a la biblioteca.",
    );
  });

  it("mostra un error si no es poden carregar els costos", async () => {
    serveis.obtenirCostosLliurament.mockRejectedValue(new Error("API aturada"));

    const element = await renderitza();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.querySelector('[role="alert"]').textContent).toBe(
      "No s'han pogut carregar els costos d'enviament.",
    );
  });

  it("buidar la comanda després d'una confirmació correcta", async () => {
    serveis.confirmaComanda.mockResolvedValue({ id: 12 });
    const element = await renderitza();
    const comanda = useComandaStore();

    element.querySelector('input[value="recollida"]').click();
    await new Promise((resolve) => setTimeout(resolve));
    element.querySelector(".confirm-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(comanda.nombreLlibres).toBe(0);
  });
});
