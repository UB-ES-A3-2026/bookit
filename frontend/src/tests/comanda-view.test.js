import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { ambRutesCompte } from "./rutesCompte.js";
import { createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ComandaView from "../views/ComandaView.vue";
import { useComandaStore } from "../stores/comanda.js";

let app;
const confirmaComanda = vi.hoisted(() => vi.fn());
const obtenirCostosLliurament = vi.hoisted(() => vi.fn());

vi.mock("../services/prestecs.js", () => ({ confirmaComanda, obtenirCostosLliurament }));

// Les comandes a domicili necessiten una adreça (US7).
async function escriuAdreca(element, adreca = "C/ Major 1") {
  const camp = element.querySelector(".camp-adreca input");
  camp.value = adreca;
  camp.dispatchEvent(new Event("input", { bubbles: true }));
  await new Promise((resolve) => setTimeout(resolve));
}

async function renderitza(llibres = []) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ambRutesCompte([
      { path: "/", name: "home", component: { template: "<p>Inici</p>" } },
      { path: "/comanda", name: "comanda", component: ComandaView },
    ]),
  });
  router.push("/comanda");
  await router.isReady();

  const pinia = createPinia();
  app = createApp(ComandaView);
  app.use(pinia);
  app.use(router);
  app.mount(document.body);

  const comanda = useComandaStore(pinia);
  llibres.forEach((llibre) => comanda.afegirLlibre(llibre));
  await new Promise((resolve) => setTimeout(resolve));
  return document.body;
}

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  sessionStorage.clear();
});

beforeEach(() => {
  vi.clearAllMocks();
  obtenirCostosLliurament.mockResolvedValue({ domicili: "2.50", recollida: "0.00" });
});

describe("La meva comanda", () => {
  it("mostra l'estructura del compte i la targeta de comanda", async () => {
    const element = await renderitza([
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
    ]);

    expect(element.querySelector(".header-quote")).not.toBeNull();
    expect(element.querySelector(".account-sidebar")).not.toBeNull();
    expect(element.querySelector("h1").textContent).toBe("La meva cistella");
    expect(element.querySelector(".order-card")).not.toBeNull();
    expect(
      element.querySelector(".resum-comanda .primary-button").textContent,
    ).toContain("Confirmar comanda");
  });

  it("mostra un missatge quan no hi ha llibres", async () => {
    const element = await renderitza();

    expect(element.textContent).toContain(
      "Encara no has afegit cap llibre a la comanda.",
    );
  });

  it("mostra els llibres afegits i permet treure'ls", async () => {
    const element = await renderitza([
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        portada: "",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
    ]);

    expect(element.textContent).toContain("La plaça del Diamant");
    element.querySelector(".secondary-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.textContent).toContain(
      "Encara no has afegit cap llibre a la comanda.",
    );
  });

  it("avisa abans de confirmar quan se supera el límit", async () => {
    const llibres = Array.from({ length: 6 }, (_, index) => ({
      id: index + 1,
      titol: `Llibre ${index + 1}`,
      autor: "Autor",
      biblioteca: { id: 3, nom: "Biblioteca" },
    }));
    const element = await renderitza(llibres);

    expect(element.textContent).toContain(
      "Has superat el límit de llibres per aquesta comanda, elimina un per continuar",
    );
    expect(element.querySelector(".resum-comanda .primary-button").disabled).toBe(true);

    element.querySelector(".resum-comanda .primary-button").click();
    await new Promise((resolve) => setTimeout(resolve));
    expect(confirmaComanda).not.toHaveBeenCalled();
  });

  it("mostra l'estoc i permet apuntar-se a la llista d'espera", async () => {
    confirmaComanda.mockRejectedValue({
      response: {
        data: {
          llibres: [
            "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera",
          ],
          sense_estoc: [7],
        },
      },
    });
    const element = await renderitza([
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
    ]);

    await escriuAdreca(element);
    element.querySelector(".resum-comanda .primary-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.textContent).toContain(
      "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera",
    );
    const waitButton = element.querySelector(".wait-button");
    waitButton.click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.textContent).toContain("Apuntat a la llista d'espera");
  });

  it("confirma correctament una comanda i buida la selecció", async () => {
    confirmaComanda.mockResolvedValue({
      id: 12,
      estat: "rebuda",
    });
    const element = await renderitza([
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
      {
        id: 9,
        titol: "Solitud",
        autor: "Víctor Català",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
    ]);

    await escriuAdreca(element);
    element.querySelector(".resum-comanda .primary-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(confirmaComanda).toHaveBeenCalledWith({
      biblioteca: 3,
      llibres: [7, 9],
      tipus_lliurament: "domicili",
      adreca_lliurament: "C/ Major 1",
    });
    expect(element.textContent).toContain(
      "Encara no has afegit cap llibre a la comanda.",
    );
  });

  it("mostra el límit exacte rebutjat pel servidor", async () => {
    confirmaComanda.mockRejectedValue({
      response: {
        data: {
          llibres: [
            "Has superat el límit de llibres per aquesta comanda, elimina un per continuar",
          ],
        },
      },
    });
    const element = await renderitza([
      {
        id: 7,
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        biblioteca: { id: 3, nom: "Biblioteca" },
      },
    ]);

    await escriuAdreca(element);
    element.querySelector(".resum-comanda .primary-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(element.textContent).toContain(
      "Has superat el límit de llibres per aquesta comanda, elimina un per continuar",
    );
  });

  it("no confirma una comanda desada sense biblioteca", async () => {
    // Una comanda desada abans que cada llibre portés la seva biblioteca (US6-T12).
    localStorage.setItem(
      "bookit.comanda",
      JSON.stringify([{ id: 7, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "" }]),
    );
    const element = await renderitza();

    element.querySelector(".resum-comanda .primary-button").click();
    await new Promise((resolve) => setTimeout(resolve));

    expect(confirmaComanda).not.toHaveBeenCalled();
    expect(element.textContent).toContain(
      "No s'ha pogut determinar la biblioteca d'aquesta comanda.",
    );
  });
});
