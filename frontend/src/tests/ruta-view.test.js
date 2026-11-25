import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { ambRutesCompte } from "./rutesCompte.js";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesRepartidors } from "../router/index.js";
import RutaView from "../views/RutaView.vue";

const servei = vi.hoisted(() => ({
  llistaRutaAvui: vi.fn(),
}));

vi.mock("../services/ruta.js", () => servei);

let wrapper;
let pinia;

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ambRutesCompte([
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/pagina", name: "pagina", component: { template: "<p />" } },
      { path: "/repartidor", name: "espai-repartidor", component: { template: "<p />" } },
    ]),
  });
  await router.push("/pagina");
  wrapper = mount(RutaView, { global: { plugins: [pinia, router] } });
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

const SOLITUD = { id: 9, titol: "Solitud", autor: "Víctor Català", portada: "" };
const PLACA = { id: 7, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "" };

function recollida(id, ordre, comanda, biblioteca = "Biblioteca Montbau") {
  return {
    id,
    ordre,
    tipus: "recollida",
    comanda,
    estat: "preparada",
    llibres: [SOLITUD],
    adreca: { biblioteca: { id: 3, nom: biblioteca }, text: null, latitud: null, longitud: null },
  };
}

function lliurament(id, ordre, comanda, text = "Carrer Major 1, Barcelona") {
  return {
    id,
    ordre,
    tipus: "lliurament",
    comanda,
    estat: "en_cami",
    llibres: [SOLITUD, PLACA],
    adreca: { biblioteca: null, text, latitud: null, longitud: null },
  };
}

// Ruta de l'exemple del contracte, amb dues comandes.
const ruta = [
  recollida(18, 1, 12),
  lliurament(19, 2, 12, "C/ Major 1"),
  recollida(20, 3, 15, "Biblioteca Central"),
  lliurament(21, 4, 15, "Avinguda Diagonal 400"),
];

const parades = () => wrapper.findAll(".parada");
const ordres = () => wrapper.findAll(".ordre").map((element) => element.text());
const tipus = () => wrapper.findAll(".tipus").map((element) => element.text());
const llocs = () => wrapper.findAll(".lloc").map((element) => element.text());

describe("Ruta del dia", () => {
  it("mostra les parades en l'ordre de la ruta", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta);
    await renderitza();

    expect(ordres()).toEqual(["1", "2", "3", "4"]);
    expect(tipus()).toEqual(["Recollida", "Lliurament", "Recollida", "Lliurament"]);
    expect(wrapper.findAll(".comanda").map((element) => element.text())).toEqual([
      "Comanda 12 · Preparada",
      "Comanda 12 · En camí",
      "Comanda 15 · Preparada",
      "Comanda 15 · En camí",
    ]);
  });

  it("ordena per `ordre` encara que l'API les enviï desordenades", async () => {
    servei.llistaRutaAvui.mockResolvedValue([ruta[3], ruta[1], ruta[2], ruta[0]]);
    await renderitza();

    expect(ordres()).toEqual(["1", "2", "3", "4"]);
    expect(llocs()).toEqual([
      "Biblioteca Montbau",
      "C/ Major 1",
      "Biblioteca Central",
      "Avinguda Diagonal 400",
    ]);
  });

  it("amb el mateix `ordre` desempata per id de parada", async () => {
    servei.llistaRutaAvui.mockResolvedValue([
      lliurament(31, 1, 20, "Segona"),
      lliurament(30, 1, 20, "Primera"),
    ]);
    await renderitza();

    expect(llocs()).toEqual(["Primera", "Segona"]);
  });

  it("no modifica la llista que rep de l'API", async () => {
    const desordenada = [ruta[1], ruta[0]];
    servei.llistaRutaAvui.mockResolvedValue(desordenada);
    await renderitza();

    expect(desordenada.map((parada) => parada.id)).toEqual([19, 18]);
  });

  it("la recollida va a la biblioteca i el lliurament a l'adreça de l'usuari", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta.slice(0, 2));
    await renderitza();

    expect(llocs()).toEqual(["Biblioteca Montbau", "C/ Major 1"]);
    expect(parades()[0].classes()).toContain("parada-recollida");
    expect(parades()[1].classes()).toContain("parada-lliurament");
  });

  it("avisa quan falta el lloc d'una parada", async () => {
    const senseBiblioteca = recollida(40, 1, 30);
    senseBiblioteca.adreca.biblioteca = null;
    servei.llistaRutaAvui.mockResolvedValue([senseBiblioteca, lliurament(41, 2, 30, null)]);
    await renderitza();

    expect(llocs()).toEqual(["Biblioteca no disponible", "Adreça no disponible"]);
  });

  it("mostra els llibres de cada parada", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta.slice(0, 2));
    await renderitza();

    expect(parades()[0].findAll(".llibres li").map((element) => element.text())).toEqual([
      "Solitud · Víctor Català",
    ]);
    expect(parades()[1].findAll(".llibres li").map((element) => element.text())).toEqual([
      "Solitud · Víctor Català",
      "La plaça del Diamant · Mercè Rodoreda",
    ]);
  });

  it("diu quantes parades hi ha", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta);
    await renderitza();
    expect(wrapper.get(".resum").text()).toBe("4 parades");
  });

  it("en singular quan només n'hi ha una", async () => {
    servei.llistaRutaAvui.mockResolvedValue([recollida(18, 1, 12)]);
    await renderitza();
    expect(wrapper.get(".resum").text()).toBe("1 parada");
  });

  it("cada parada diu la seva posició als lectors de pantalla", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta.slice(0, 2));
    await renderitza();

    expect(wrapper.findAll(".parada h2").map((element) => element.text())).toEqual([
      "Parada 1: Recollida",
      "Parada 2: Lliurament",
    ]);
  });

  it("mostra que està carregant", async () => {
    servei.llistaRutaAvui.mockReturnValue(new Promise(() => {}));
    await renderitza();

    expect(wrapper.get('[role="status"]').text()).toBe("Carregant la ruta...");
    expect(wrapper.find(".llista-parades").exists()).toBe(false);
  });

  it("avisa quan avui no hi ha parades", async () => {
    servei.llistaRutaAvui.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.text()).toContain("Avui no tens cap parada.");
    expect(wrapper.find(".llista-parades").exists()).toBe(false);
    expect(wrapper.find(".resum").exists()).toBe(false);
  });

  it("mostra l'error i permet tornar-ho a provar", async () => {
    servei.llistaRutaAvui.mockRejectedValueOnce(new Error("Network Error"));
    await renderitza();
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "No s'ha pogut carregar la teva ruta. Torna-ho a provar més tard.",
    );

    servei.llistaRutaAvui.mockResolvedValueOnce(ruta);
    await wrapper.get(".secondary-button").trigger("click");
    await flushPromises();

    expect(servei.llistaRutaAvui).toHaveBeenCalledTimes(2);
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(parades()).toHaveLength(4);
  });

  it("explica el 409 de dades inconsistents", async () => {
    servei.llistaRutaAvui.mockRejectedValue({
      response: { status: 409, data: { detail: "La ruta conté dades inconsistents." } },
    });
    await renderitza();

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "La teva ruta d'avui té dades inconsistents. Avisa l'equip de bookit.",
    );
  });

  it("torna a l'inici si l'API respon 403", async () => {
    servei.llistaRutaAvui.mockRejectedValue({ response: { status: 403 } });
    const router = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
  });

  it("tancar la sessió la tanca i torna a l'inici", async () => {
    servei.llistaRutaAvui.mockResolvedValue([]);
    const sessio = useSessioStore();
    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "repartidor" });
    const router = await renderitza();

    await wrapper.get(".logout-button").trigger("click");
    await flushPromises();

    expect(sessio.autenticat).toBe(false);
    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("accés a la ruta", () => {
  it("està protegida només per a repartidors", () => {
    const ruta = router.resolve("/repartidor/ruta");
    expect(ruta.name).toBe("ruta-repartidor");
    expect(ruta.matched[0].beforeEnter).toBe(nomesRepartidors);
  });

  it("demana iniciar sessió si no n'hi ha cap", () => {
    expect(nomesRepartidors()).toEqual({ name: "inici-sessio" });
  });

  it("deixa entrar el rol repartidor", () => {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "repartidor" });
    expect(nomesRepartidors()).toBe(true);
  });

  it("torna a l'inici amb un altre rol", () => {
    const sessio = useSessioStore();

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });
    expect(nomesRepartidors()).toEqual({ name: "home" });

    sessio.iniciarSessio({ accessToken: "token-de-prova", rol: "biblioteca" });
    expect(nomesRepartidors()).toEqual({ name: "home" });
  });
});

describe("mapa de la ruta (US12-T7)", () => {
  it("mostra el mapa a sobre de la llista amb les parades que tenen ubicació", async () => {
    servei.llistaRutaAvui.mockResolvedValue([
      { ...ruta[0], adreca: { ...ruta[0].adreca, latitud: 41.386016, longitud: 2.169408 } },
      { ...ruta[1], adreca: { ...ruta[1].adreca, latitud: 41.403629, longitud: 2.174355 } },
      ruta[2],
      ruta[3],
    ]);
    await renderitza();

    expect(wrapper.find('[data-testid="mapa-parades"]').exists()).toBe(true);
    expect(wrapper.findAll(".marcador-parada")).toHaveLength(2);
    expect(wrapper.find(".avis-mapa").text()).toContain("2 parades no surten al mapa");
    // Les parades sense ubicació continuen a la llista.
    expect(parades()).toHaveLength(4);
  });

  it("sense ubicacions mostra la llista i l'avís, però no el mapa", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta);
    await renderitza();

    expect(wrapper.find('[data-testid="mapa-parades"]').exists()).toBe(false);
    expect(wrapper.find(".avis-mapa").exists()).toBe(true);
    expect(parades()).toHaveLength(4);
  });

  it("si avui no hi ha parades no mostra ni el mapa ni l'avís", async () => {
    servei.llistaRutaAvui.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.find(".mapa-parades").exists()).toBe(false);
  });
});
