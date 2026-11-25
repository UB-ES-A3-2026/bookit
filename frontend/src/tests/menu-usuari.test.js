import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import MenuUsuari from "../components/MenuUsuari.vue";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";

const buida = { render: () => null };
const NOMS_RUTES = [
  "home",
  "meves-comandes",
  "comanda",
  "prestecs",
  "adreces",
  "cataleg",
  "cataleg-afegir",
  "comandes-biblioteca",
  "espai-repartidor",
  "ruta-repartidor",
  "franges-repartidor",
];

let wrapper;
let pinia;

async function renderitza({ rol = "usuari", usuari = { nom: "Laia Vidal" } } = {}) {
  useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol, usuari });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: NOMS_RUTES.map((name, index) => ({
      path: index === 0 ? "/" : `/${name}`,
      name,
      component: buida,
    })),
  });
  await router.push("/");
  await router.isReady();
  wrapper = mount(MenuUsuari, {
    attachTo: document.body,
    global: { plugins: [pinia, router] },
  });
  await flushPromises();
  return router;
}

const textosEnllacos = () =>
  wrapper.findAll(".menu-usuari__enllac").map((enllac) => enllac.text());

beforeEach(() => {
  sessionStorage.clear();
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  document.body.innerHTML = "";
});

describe("menú de l'usuari de la capçalera", () => {
  it("mostra un botó amb el nom, les inicials i el rol, amb el menú tancat", async () => {
    await renderitza();

    const boto = wrapper.get(".menu-usuari__boto");
    expect(boto.text()).toContain("Laia Vidal");
    expect(boto.text()).toContain("LV");
    expect(boto.text()).toContain("Usuari");
    expect(boto.attributes("aria-expanded")).toBe("false");
    expect(wrapper.find(".menu-usuari__panell").exists()).toBe(false);
  });

  it("en clicar el botó desplega les seccions de l'usuari", async () => {
    await renderitza();

    await wrapper.get(".menu-usuari__boto").trigger("click");

    expect(wrapper.get(".menu-usuari__boto").attributes("aria-expanded")).toBe("true");
    expect(textosEnllacos()).toEqual([
      "Les meves comandes",
      "La meva cistella",
      "Els meus préstecs",
      "Les meves adreces",
    ]);
  });

  it("mostra quants llibres hi ha a la cistella", async () => {
    await renderitza();
    useComandaStore().llibres = [{ id: 1 }, { id: 2 }];

    await wrapper.get(".menu-usuari__boto").trigger("click");

    expect(wrapper.get(".menu-usuari__comptador").text()).toBe("2");
  });

  it("mostra les seccions de la biblioteca", async () => {
    await renderitza({ rol: "biblioteca", usuari: { nom: "Biblioteca Sant Gervasi" } });

    await wrapper.get(".menu-usuari__boto").trigger("click");

    expect(wrapper.get(".menu-usuari__boto").text()).toContain("Biblioteca");
    expect(textosEnllacos()).toEqual([
      "El meu catàleg",
      "Afegir un llibre",
      "Comandes pendents",
    ]);
  });

  it("mostra les seccions del repartidor", async () => {
    await renderitza({ rol: "repartidor", usuari: { nom: "Pau" } });

    await wrapper.get(".menu-usuari__boto").trigger("click");

    expect(textosEnllacos()).toEqual([
      "Espai del repartidor",
      "La meva ruta d'avui",
      "Franges de disponibilitat",
    ]);
  });

  it("fa servir el correu si l'usuari no té nom", async () => {
    await renderitza({ usuari: { correu: "laia@example.cat" } });

    expect(wrapper.get(".menu-usuari__boto").text()).toContain("laia@example.cat");
  });

  it("es tanca en navegar a una secció", async () => {
    const router = await renderitza();
    await wrapper.get(".menu-usuari__boto").trigger("click");

    await wrapper.get('a[href="/prestecs"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("prestecs");
    expect(wrapper.find(".menu-usuari__panell").exists()).toBe(false);
  });

  it("es tanca amb Escape i en clicar fora", async () => {
    await renderitza();
    const boto = wrapper.get(".menu-usuari__boto");

    await boto.trigger("click");
    await wrapper.get(".menu-usuari").trigger("keydown", { key: "Escape" });
    expect(wrapper.find(".menu-usuari__panell").exists()).toBe(false);

    await boto.trigger("click");
    document.body.click();
    await flushPromises();
    expect(wrapper.find(".menu-usuari__panell").exists()).toBe(false);
  });
});
