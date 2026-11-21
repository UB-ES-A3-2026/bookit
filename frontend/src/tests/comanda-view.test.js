import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia } from "pinia";
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

describe("selector de lliurament", () => {
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
});
