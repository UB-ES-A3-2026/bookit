import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import LayoutCompte from "../components/LayoutCompte.vue";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";
import { rutesCompte } from "./rutesCompte.js";

vi.mock("../services/notificacions.js", () => ({
  llistaNotificacions: vi.fn(async () => []),
  marcaLlegida: vi.fn(),
  marcaTotesLlegides: vi.fn(),
}));

let wrapper;
let pinia;
let router;

async function renderitza({ props = {}, slots = {}, ruta = "/comandes" } = {}) {
  useSessioStore().iniciarSessio({
    accessToken: "token-de-prova",
    rol: "usuari",
    usuari: { nom: "Laia Vidal", correu: "laia.vidal@email.cat" },
  });
  router = createRouter({ history: createMemoryHistory(), routes: rutesCompte });
  await router.push(ruta);
  await router.isReady();
  wrapper = mount(LayoutCompte, {
    props: { titol: "Les meves comandes", apartat: "Comandes", ...props },
    slots: { default: "<p class='contingut'>Contingut</p>", ...slots },
    attachTo: document.body,
    global: { plugins: [pinia, router] },
  });
  await flushPromises();
}

const enllacosBarra = () => wrapper.findAll(".account-nav__link");

beforeEach(() => {
  sessionStorage.clear();
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  document.body.innerHTML = "";
});

describe("estructura de les pàgines del compte", () => {
  it("mostra la capçalera, la barra lateral i el contingut de la pàgina", async () => {
    await renderitza();

    expect(wrapper.find("header .menu-usuari__boto").exists()).toBe(true);
    expect(wrapper.find("header .notificacions-boto").exists()).toBe(true);
    expect(wrapper.find("header .logout-button").exists()).toBe(true);
    expect(wrapper.get(".profile-summary").text()).toContain("Laia Vidal");
    expect(wrapper.get(".profile-summary").text()).toContain("laia.vidal@email.cat");
    expect(wrapper.get("main .contingut").text()).toBe("Contingut");
  });

  it("mostra el títol, l'apartat i la descripció", async () => {
    await renderitza({ props: { descripcio: "Consulta les comandes." } });

    expect(wrapper.get("h1").text()).toBe("Les meves comandes");
    expect(wrapper.get(".breadcrumb").text()).toContain("El meu compte");
    expect(wrapper.get(".breadcrumb").text()).toContain("Comandes");
    expect(wrapper.get(".description").text()).toBe("Consulta les comandes.");
  });

  it("no mostra la descripció ni les accions si no se'n passen", async () => {
    await renderitza();

    expect(wrapper.find(".description").exists()).toBe(false);
    expect(wrapper.find(".page-heading__accions").exists()).toBe(false);
  });

  it("posa les accions al costat del títol", async () => {
    await renderitza({ slots: { accions: "<button class='accio'>Afegir</button>" } });

    expect(wrapper.get(".page-heading__accions .accio").text()).toBe("Afegir");
  });

  it("la barra lateral enllaça a totes les seccions del compte", async () => {
    await renderitza();

    expect(enllacosBarra().map((enllac) => enllac.text())).toEqual([
      "Les meves comandes",
      "La meva cistella",
      "Els meus préstecs",
      "Adreces de lliurament",
      "Tornar a l'inici",
    ]);
    expect(enllacosBarra().map((enllac) => enllac.attributes("href"))).toEqual([
      "/comandes",
      "/comanda",
      "/prestecs",
      "/adreces",
      "/",
    ]);
  });

  it("marca la secció de la pàgina actual", async () => {
    await renderitza({ ruta: "/prestecs" });

    const actius = wrapper.findAll(".account-nav__link.router-link-exact-active");
    expect(actius.map((enllac) => enllac.text())).toEqual(["Els meus préstecs"]);
  });

  it("navega en clicar una secció", async () => {
    await renderitza();

    await wrapper.get('.account-nav a[href="/adreces"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("adreces");
  });

  it("mostra quants llibres hi ha a la cistella", async () => {
    await renderitza();
    useComandaStore().llibres = [{ id: 1 }, { id: 2 }, { id: 3 }];
    await flushPromises();

    expect(wrapper.get(".account-nav__count").text()).toBe("3");
  });

  it("tanca la sessió i torna a l'inici", async () => {
    await renderitza();

    await wrapper.get(".logout-button").trigger("click");
    await flushPromises();

    expect(useSessioStore().autenticat).toBe(false);
    expect(router.currentRoute.value.name).toBe("home");
  });
});
