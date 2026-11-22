import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesBiblioteques } from "../router/index.js";
import ComandesBibliotecaView from "../views/ComandesBibliotecaView.vue";

const servei = vi.hoisted(() => ({
  llistaComandesBiblioteca: vi.fn(),
}));

vi.mock("../services/comandesBiblioteca.js", () => servei);

let wrapper;
let pinia;

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/pagina", name: "pagina", component: { template: "<p />" } },
      { path: "/cataleg", name: "cataleg", component: { template: "<p />" } },
    ],
  });
  await router.push("/pagina");
  wrapper = mount(ComandesBibliotecaView, { global: { plugins: [pinia, router] } });
  await flushPromises();
  return router;
}

beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

function comanda(id, estat, data_lliurament) {
  return {
    id,
    estat,
    data_lliurament,
    usuari: { id: 25, nom: "Anna Puig" },
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 9, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    creada: "2026-11-16T12:20:00Z",
  };
}

// L'ordre no és el dels id: és el que envia l'API.
const comandes = [
  comanda(12, "rebuda", "2026-11-20"),
  comanda(4, "preparada", "2026-11-28"),
  comanda(8, "cancellada", null),
];

describe("Comandes pendents", () => {
  it("mostra els llibres, l'usuari i la data de lliurament", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    await renderitza();

    const text = wrapper.get(".comanda").text();
    expect(text).toContain("Solitud");
    expect(text).toContain("Víctor Català");
    expect(text).toContain("Anna Puig");
    expect(text).toContain("20/11/2026");
  });

  it("manté l'ordre de l'API", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    await renderitza();

    expect(wrapper.findAll(".comanda h2").map((titol) => titol.text())).toEqual([
      "Comanda 12",
      "Comanda 4",
      "Comanda 8",
    ]);
    expect(wrapper.findAll(".data-lliurament").at(-1).text()).toBe("Sense data");
  });

  it("mostra els estats i avisa de les cancel·lades", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    await renderitza();

    expect(wrapper.findAll(".etiqueta").map((element) => element.text())).toEqual([
      "Rebuda",
      "Preparada",
      "Cancel·lada",
    ]);
    expect(wrapper.findAll(".avis-cancellada")).toHaveLength(1);
  });

  it("mostra que està carregant", async () => {
    servei.llistaComandesBiblioteca.mockReturnValue(new Promise(() => {}));
    await renderitza();

    expect(wrapper.get('[role="status"]').text()).toBe("Carregant les comandes...");
  });

  it("avisa quan no n'hi ha cap", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.text()).toContain("No tens cap comanda pendent.");
    expect(wrapper.find(".llista-comandes").exists()).toBe(false);
  });

  it("mostra l'error i permet tornar-ho a provar", async () => {
    servei.llistaComandesBiblioteca.mockRejectedValueOnce(new Error("Network Error"));
    await renderitza();
    expect(wrapper.get('[role="alert"]').text()).toContain("No s'han pogut carregar les comandes.");

    servei.llistaComandesBiblioteca.mockResolvedValueOnce(comandes);
    await wrapper.get(".secondary-button").trigger("click");
    await flushPromises();

    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(wrapper.findAll(".comanda")).toHaveLength(comandes.length);
  });

  it("torna a l'inici si l'API respon 403", async () => {
    servei.llistaComandesBiblioteca.mockRejectedValue({ response: { status: 403 } });
    const router = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("accés a la ruta", () => {
  it("està protegida", () => {
    expect(router.resolve("/biblioteca/comandes").matched[0].beforeEnter).toBe(nomesBiblioteques);
  });

  it("demana iniciar sessió si no n'hi ha cap", () => {
    expect(nomesBiblioteques()).toEqual({ name: "inici-sessio" });
  });

  it("deixa entrar el rol biblioteca", () => {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "biblioteca" });
    expect(nomesBiblioteques()).toBe(true);
  });

  it("torna a l'inici amb un altre rol", () => {
    const sessio = useSessioStore();

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });
    expect(nomesBiblioteques()).toEqual({ name: "home" });

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "repartidor" });
    expect(nomesBiblioteques()).toEqual({ name: "home" });
  });
});
