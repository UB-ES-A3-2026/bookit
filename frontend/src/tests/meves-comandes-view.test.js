import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesUsuaris } from "../router/index.js";
import MevesComandesView from "../views/MevesComandesView.vue";

const servei = vi.hoisted(() => ({
  llistaMevesComandes: vi.fn(),
}));

vi.mock("../services/comandesUsuari.js", () => servei);

const notificacions = vi.hoisted(() => ({
  llistaNotificacions: vi.fn(),
}));

vi.mock("../services/notificacions.js", () => notificacions);

let wrapper;
let pinia;

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/pagina", name: "pagina", component: { template: "<p />" } },

    ],
  });
  await router.push("/pagina");
  wrapper = mount(MevesComandesView, { global: { plugins: [pinia, router] } });
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

function comanda(id, estat, data_lliurament = null) {
  return {
    id,
    estat,
    data_lliurament,
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 9, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    creada: "2026-11-16T12:20:00Z",
  };
}

const comandes = [
  comanda(15, "rebuda"),
  comanda(14, "preparada", "2026-11-24"),
  comanda(13, "en_cami", "2026-11-22"),
  comanda(12, "lliurada", "2026-11-20"),
  comanda(11, "cancellada"),
];

describe("Les meves comandes", () => {
  it("mostra l'estat de cada comanda amb el text per a l'usuari", async () => {
    servei.llistaMevesComandes.mockResolvedValue(comandes);
    await renderitza();

    expect(wrapper.findAll(".etiqueta").map((element) => element.text())).toEqual([
      "Rebuda",
      "Preparada",
      "En camí",
      "Lliurada",
      "Cancel·lada",
    ]);
  });

  it("mostra la biblioteca, els llibres i la data de la comanda", async () => {
    servei.llistaMevesComandes.mockResolvedValue(comandes);
    await renderitza();

    const text = wrapper.get(".comanda").text();
    expect(text).toContain("Biblioteca Montbau");
    expect(text).toContain("Solitud");
    expect(text).toContain("16/11/2026");
  });

  it("diu quan arribarà, si ja se sap", async () => {
    servei.llistaMevesComandes.mockResolvedValue(comandes);
    await renderitza();

    const files = wrapper.findAll(".comanda");
    expect(files[0].get(".data-lliurament").text()).toBe("Sense data");
    expect(files[1].text()).toContain("Lliurament previst");
    expect(files[1].get(".data-lliurament").text()).toBe("24/11/2026");
    expect(files[3].text()).toContain("Data de lliurament");
    expect(files[4].find(".data-lliurament").exists()).toBe(false);
  });

  it("té les notificacions a la capçalera", async () => {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });
    servei.llistaMevesComandes.mockResolvedValue(comandes);
    notificacions.llistaNotificacions.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.find("header .notificacions-boto").exists()).toBe(true);
  });

  it("mostra que està carregant", async () => {
    servei.llistaMevesComandes.mockReturnValue(new Promise(() => {}));
    await renderitza();

    expect(wrapper.get('[role="status"]').text()).toBe("Carregant les comandes...");
  });

  it("avisa quan no n'hi ha cap", async () => {
    servei.llistaMevesComandes.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.text()).toContain("Encara no has fet cap comanda.");
    expect(wrapper.find(".llista-comandes").exists()).toBe(false);
  });

  it("mostra l'error i permet tornar-ho a provar", async () => {
    servei.llistaMevesComandes.mockRejectedValueOnce(new Error("Network Error"));
    await renderitza();
    expect(wrapper.get('[role="alert"]').text()).toContain("No s'han pogut carregar les teves comandes.");

    servei.llistaMevesComandes.mockResolvedValueOnce(comandes);
    await wrapper.get(".secondary-button").trigger("click");
    await flushPromises();

    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(wrapper.findAll(".comanda")).toHaveLength(comandes.length);
  });

  it("torna a l'inici si l'API respon 403", async () => {
    servei.llistaMevesComandes.mockRejectedValue({ response: { status: 403 } });
    const router = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("accés a la ruta", () => {
  it("està protegida", () => {
    expect(router.resolve("/comandes").matched[0].beforeEnter).toBe(nomesUsuaris);
  });

  it("demana iniciar sessió si no n'hi ha cap", () => {
    expect(nomesUsuaris()).toEqual({ name: "inici-sessio" });
  });

  it("deixa entrar el rol usuari", () => {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });
    expect(nomesUsuaris()).toBe(true);
  });

  it("torna a l'inici amb un altre rol", () => {
    const sessio = useSessioStore();

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "biblioteca" });
    expect(nomesUsuaris()).toEqual({ name: "home" });

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "repartidor" });
    expect(nomesUsuaris()).toEqual({ name: "home" });
  });
});
