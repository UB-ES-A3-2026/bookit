import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ComandaView from "../views/ComandaView.vue";
import { useComandaStore } from "../stores/comanda.js";

let app;
const confirmaComanda = vi.hoisted(() => vi.fn());

vi.mock("../services/prestecs.js", () => ({ confirmaComanda }));

async function renderitza(llibres = []) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p>Inici</p>" } },
      { path: "/comanda", name: "comanda", component: ComandaView },
    ],
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
});

describe("La meva comanda", () => {
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
});
