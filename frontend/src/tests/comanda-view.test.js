import { createApp } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { createPinia } from "pinia";
import { afterEach, describe, expect, it } from "vitest";
import ComandaView from "../views/ComandaView.vue";
import { useComandaStore } from "../stores/comanda.js";

let app;

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
});
