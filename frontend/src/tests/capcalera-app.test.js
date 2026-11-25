import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CapcaleraApp from "../components/CapcaleraApp.vue";
import { useSessioStore } from "../stores/sessio.js";
import { rutesCompte } from "./rutesCompte.js";

vi.mock("../services/notificacions.js", () => ({
  llistaNotificacions: vi.fn(async () => []),
  marcaLlegida: vi.fn(),
  marcaTotesLlegides: vi.fn(),
}));

let wrapper;
let router;

async function renderitza(rol) {
  if (rol) {
    useSessioStore().iniciarSessio({
      accessToken: "token-de-prova",
      rol,
      usuari: { nom: "Laia Vidal" },
    });
  }
  router = createRouter({ history: createMemoryHistory(), routes: rutesCompte });
  await router.push("/comandes");
  await router.isReady();
  wrapper = mount(CapcaleraApp, {
    attachTo: document.body,
    global: { plugins: [router] },
  });
  await flushPromises();
}

beforeEach(() => {
  sessionStorage.clear();
  setActivePinia(createPinia());
});

afterEach(() => {
  wrapper?.unmount();
  document.body.innerHTML = "";
});

describe("capçalera comuna de les pàgines amb sessió", () => {
  it.each([
    ["usuari", "Catàleg", "/cerca"],
    ["biblioteca", "El meu catàleg", "/cataleg"],
    ["repartidor", "La meva ruta", "/repartidor/ruta"],
  ])("amb el rol %s l'enllaç principal és «%s»", async (rol, text, href) => {
    await renderitza(rol);

    const enllac = wrapper.get(".catalog-link");
    expect(enllac.text()).toBe(text);
    expect(enllac.attributes("href")).toBe(href);
  });

  it.each(["usuari", "biblioteca", "repartidor"])(
    "amb el rol %s mostra el menú de l'usuari i el botó de tancar sessió",
    async (rol) => {
      await renderitza(rol);

      expect(wrapper.get(".menu-usuari__boto").text()).toContain("Laia Vidal");
      expect(wrapper.get(".logout-button").text()).toBe("Tancar sessió");
    },
  );

  it("només els usuaris veuen la campaneta de notificacions", async () => {
    await renderitza("usuari");
    expect(wrapper.find(".notificacions-boto").exists()).toBe(true);
    wrapper.unmount();

    setActivePinia(createPinia());
    await renderitza("biblioteca");
    expect(wrapper.find(".notificacions-boto").exists()).toBe(false);
  });

  it("sense rol no mostra cap enllaç principal", async () => {
    await renderitza(null);

    expect(wrapper.find(".catalog-link").exists()).toBe(false);
  });

  it("tancar la sessió la tanca i torna a l'inici", async () => {
    await renderitza("biblioteca");

    await wrapper.get(".logout-button").trigger("click");
    await flushPromises();

    expect(useSessioStore().autenticat).toBe(false);
    expect(router.currentRoute.value.name).toBe("home");
  });
});
