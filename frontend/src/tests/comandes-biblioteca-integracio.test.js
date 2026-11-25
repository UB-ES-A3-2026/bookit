import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.vue";
import router from "../router/index.js";
import { useSessioStore } from "../stores/sessio.js";

// Vistes, router i serveis de veritat: només se simula el client HTTP.
const api = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock("../services/api.js", () => ({ default: api }));

let wrapper;
let pinia;

async function obre(ruta, rol) {
  if (rol) {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol });
  }
  await router.push(ruta);
  wrapper = mount(App, { global: { plugins: [pinia, router] } });
  await flushPromises();
}

async function clica(selector) {
  await wrapper.get(selector).trigger("click");
  await flushPromises();
}

beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  vi.unstubAllEnvs();
});

const RUTA_API = "/prestecs/biblioteca/comandes/";

function comanda(id, data_lliurament, canvis = {}) {
  return {
    id,
    estat: "rebuda",
    data_lliurament,
    usuari: { id: 25, nom: "Anna Puig" },
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 9, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    creada: "2026-11-16T12:20:00Z",
    ...canvis,
  };
}

function respon(comandes) {
  api.get.mockImplementation(async (url) => ({ data: url === RUTA_API ? comandes : [] }));
}

const numeros = () =>
  wrapper.findAll(".comanda h2").map((titol) => Number(titol.text().replace("Comanda ", "")));
const dates = () => wrapper.findAll(".data-lliurament").map((data) => data.text());

describe("ordre de les comandes pendents (CP-US10-01)", () => {
  it("de la data més propera a la més llunyana, també si canvia el mes o l'any", async () => {
    // Ordenades com a text DD/MM/AAAA quedarien al revés.
    respon([comanda(3, "2026-11-30"), comanda(1, "2026-12-02"), comanda(2, "2027-01-01")]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(numeros()).toEqual([3, 1, 2]);
    expect(dates()).toEqual(["30/11/2026", "02/12/2026", "01/01/2027"]);
  });

  it("les que no tenen data es queden al final", async () => {
    respon([comanda(8, "2026-11-25"), comanda(2, null), comanda(5, null)]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(numeros()).toEqual([8, 2, 5]);
    expect(dates()).toEqual(["25/11/2026", "Sense data", "Sense data"]);
  });

  it("amb la mateixa data surt primer la més antiga, encara que tingui un id més alt", async () => {
    respon([
      comanda(9, "2026-11-25", { creada: "2026-11-10T09:00:00Z" }),
      comanda(4, "2026-11-25", { creada: "2026-11-12T09:00:00Z" }),
    ]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(numeros()).toEqual([9, 4]);
  });

  it("l'estat no altera l'ordre per data", async () => {
    respon([
      comanda(1, "2026-11-23", { estat: "cancellada" }),
      comanda(2, "2026-11-24", { estat: "preparada" }),
      comanda(3, "2026-11-25", { estat: "rebuda" }),
    ]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(numeros()).toEqual([1, 2, 3]);
  });

  it("en tornar a entrar mostra l'ordre nou", async () => {
    respon([comanda(1, "2026-11-23"), comanda(2, "2026-11-24")]);
    await obre("/biblioteca/comandes", "biblioteca");
    expect(numeros()).toEqual([1, 2]);

    await router.push("/cataleg");
    await flushPromises();
    respon([comanda(2, "2026-11-22"), comanda(1, "2026-11-23")]);
    await router.push("/biblioteca/comandes");
    await flushPromises();

    expect(numeros()).toEqual([2, 1]);
  });
});

describe("dades de la llista (CP-US10-05)", () => {
  it("demana les comandes a l'endpoint de la biblioteca", async () => {
    respon([]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(api.get).toHaveBeenCalledExactlyOnceWith(RUTA_API);
  });

  it("mostra tots els llibres de cada comanda sense barrejar-los", async () => {
    const llibre = (id, titol) => ({ id, titol, autor: "Autor de prova", portada: "" });
    respon([
      comanda(1, null, { llibres: [llibre(7, "La plaça del Diamant"), llibre(9, "Solitud")] }),
      comanda(2, null, { llibres: [llibre(4, "Incerta glòria")] }),
    ]);
    await obre("/biblioteca/comandes", "biblioteca");

    const titols = wrapper
      .findAll(".comanda")
      .map((fila) => fila.findAll(".titol").map((titol) => titol.text()));
    expect(titols).toEqual([["La plaça del Diamant", "Solitud"], ["Incerta glòria"]]);
  });

  it.each(["America/Los_Angeles", "Europe/Madrid", "Pacific/Kiritimati"])(
    "la data de lliurament no canvia de dia a %s",
    async (zona) => {
      vi.stubEnv("TZ", zona);
      respon([comanda(1, "2026-11-20")]);
      await obre("/biblioteca/comandes", "biblioteca");

      expect(dates()).toEqual(["20/11/2026"]);
    },
  );

  it("el dia de la comanda és el de l'hora local", async () => {
    vi.stubEnv("TZ", "Europe/Madrid");
    respon([comanda(1, null, { creada: "2026-11-16T23:30:00Z" })]);
    await obre("/biblioteca/comandes", "biblioteca");

    expect(wrapper.get(".comanda").text()).toContain("17/11/2026");
  });
});

describe("navegació", () => {
  it("s'hi arriba des del menú de l'usuari al catàleg", async () => {
    respon([comanda(12, null)]);
    await obre("/cataleg", "biblioteca");
    await clica(".menu-usuari__boto");
    await clica('a[href="/biblioteca/comandes"]');

    await vi.waitFor(() => expect(numeros()).toEqual([12]));
  });

  it.each([
    [null, "inici-sessio"],
    ["usuari", "home"],
    ["repartidor", "home"],
  ])("amb el rol %s no es demana cap comanda", async (rol, desti) => {
    respon([]);
    await obre("/biblioteca/comandes", rol);

    expect(router.currentRoute.value.name).toBe(desti);
    expect(api.get).not.toHaveBeenCalledWith(RUTA_API);
  });
});
