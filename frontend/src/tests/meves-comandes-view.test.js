import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { ambRutesCompte } from "./rutesCompte.js";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesUsuaris } from "../router/index.js";
import MevesComandesView from "../views/MevesComandesView.vue";

const servei = vi.hoisted(() => ({
  llistaMevesComandes: vi.fn(),
  cancellaComanda: vi.fn(),
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
    routes: ambRutesCompte([
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/pagina", name: "pagina", component: { template: "<p />" } },
    ]),
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
  vi.restoreAllMocks();
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

  it("demana confirmació amb el text exacte abans de cancel·lar", async () => {
    servei.llistaMevesComandes.mockResolvedValue([comanda(15, "rebuda")]);
    servei.cancellaComanda.mockResolvedValue(comanda(15, "cancellada"));
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await renderitza();

    await wrapper.get(".cancel-button").trigger("click");
    await flushPromises();

    expect(window.confirm).toHaveBeenCalledWith(
      "Segur que vols cancel·lar aquesta comanda?",
    );
    expect(servei.cancellaComanda).toHaveBeenCalledWith(15);
  });

  it("no envia la petició si l'usuari rebutja la confirmació", async () => {
    servei.llistaMevesComandes.mockResolvedValue([comanda(15, "rebuda")]);
    vi.spyOn(window, "confirm").mockReturnValue(false);
    await renderitza();

    await wrapper.get(".cancel-button").trigger("click");

    expect(servei.cancellaComanda).not.toHaveBeenCalled();
    expect(wrapper.get(".etiqueta").text()).toBe("Rebuda");
  });

  it("actualitza la comanda quan la cancel·lació té èxit", async () => {
    servei.llistaMevesComandes.mockResolvedValue([comanda(15, "preparada")]);
    servei.cancellaComanda.mockResolvedValue(comanda(15, "cancellada"));
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await renderitza();

    await wrapper.get(".cancel-button").trigger("click");
    await flushPromises();

    expect(wrapper.get(".etiqueta").text()).toBe("Cancel·lada");
    expect(wrapper.find(".cancel-button").exists()).toBe(false);
  });

  it("mostra l'avís exacte si la comanda ja ha sortit", async () => {
    servei.llistaMevesComandes.mockResolvedValue([
      comanda(15, "en_cami"),
      comanda(14, "lliurada"),
    ]);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await renderitza();

    const buttons = wrapper.findAll(".cancel-button");
    await buttons[0].trigger("click");
    await buttons[1].trigger("click");

    expect(wrapper.findAll('[role="alert"]').map((alert) => alert.text())).toEqual([
      "Aquesta comanda ja ha sortit i no es pot cancel·lar",
      "Aquesta comanda ja ha sortit i no es pot cancel·lar",
    ]);
    expect(window.confirm).not.toHaveBeenCalled();
    expect(servei.cancellaComanda).not.toHaveBeenCalled();
  });

  it("mostra l'avís retornat pel servidor si l'estat ha canviat", async () => {
    servei.llistaMevesComandes.mockResolvedValue([comanda(15, "rebuda")]);
    servei.cancellaComanda.mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "Aquesta comanda ja ha sortit i no es pot cancel·lar" },
      },
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await renderitza();

    await wrapper.get(".cancel-button").trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe(
      "Aquesta comanda ja ha sortit i no es pot cancel·lar",
    );
    expect(wrapper.get(".etiqueta").text()).toBe("Rebuda");
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

  it("té la targeta de l'usuari a la capçalera", async () => {
    useSessioStore().iniciarSessio({
      accessToken: "token-de-prova",
      rol: "usuari",
      usuari: { nom: "Laia Vidal" },
    });
    servei.llistaMevesComandes.mockResolvedValue(comandes);
    notificacions.llistaNotificacions.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.get("header .menu-usuari__boto").text()).toContain("Laia Vidal");
    expect(wrapper.find("header .logout-button").exists()).toBe(true);
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

  it("una comanda de recollida diu que es recull a la biblioteca en lloc de la data", async () => {
    servei.llistaMevesComandes.mockResolvedValue([
      { ...comanda(12, "preparada", null), tipus_lliurament: "recollida" },
      { ...comanda(4, "preparada", null), tipus_lliurament: "domicili" },
    ]);
    await renderitza();

    const dates = wrapper.findAll(".data-lliurament").map((data) => data.text());
    expect(dates).toEqual(["Recollida a la biblioteca", "Sense data"]);
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
