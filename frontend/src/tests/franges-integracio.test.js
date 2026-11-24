import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.vue";
import router from "../router/index.js";
import { useSessioStore } from "../stores/sessio.js";

// Vistes, router i serveis de veritat: només se simula el client HTTP.
const api = vi.hoisted(() => ({
  get: vi.fn(),
  put: vi.fn(),
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
  // Les altres peticions (per exemple, les notificacions de la capçalera, US8) reben una llista buida.
  api.get.mockResolvedValue({ data: [] });
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  vi.unstubAllEnvs();
});

const RUTA_API = "/usuaris/repartidor/franges/";

const franja = (dia, hora_inici, hora_fi) => ({ dia, hora_inici, hora_fi });
const error400 = (franges) => ({ response: { status: 400, data: { franges } } });
const dia = (index) => wrapper.findAll(".dia")[index];
const horesDelDia = (index) => dia(index).findAll("input").map((camp) => camp.element.value);

function respon(franges) {
  api.get.mockImplementation(async (ruta) =>
    ruta === RUTA_API
      ? { data: { franges: franges.map((dades, index) => ({ id: index + 4, ...dades })) } }
      : { data: [] },
  );
}

async function afegeix(index, inici = "", fi = "") {
  await dia(index).get(".afegeix").trigger("click");
  const camps = dia(index).findAll("input");
  await camps.at(-2).setValue(inici);
  await camps.at(-1).setValue(fi);
}

async function desa() {
  await wrapper.get("form").trigger("submit");
  await flushPromises();
}

const enviades = () => api.put.mock.calls.at(-1)[1].franges;

beforeEach(() => {
  respon([franja(0, "09:00", "13:00"), franja(4, "09:00", "14:30")]);
  api.put.mockImplementation(async (url, cos) => ({ data: cos }));
});

describe("selecció de les franges (CP-US14-02)", () => {
  it.each([
    [0, "Dilluns"],
    [1, "Dimarts"],
    [2, "Dimecres"],
    [3, "Dijous"],
    [4, "Divendres"],
    [5, "Dissabte"],
    [6, "Diumenge"],
  ])("el dia %i de l'API és %s", async (numero, nom) => {
    respon([]);
    await obre("/repartidor/franges", "repartidor");
    expect(dia(numero).get("h2").text()).toBe(nom);

    await afegeix(numero, "10:00", "12:00");
    await desa();

    expect(enviades()).toEqual([franja(numero, "10:00", "12:00")]);
  });

  it("mostra diverses franges del mateix dia", async () => {
    respon([franja(2, "09:00", "13:00"), franja(2, "16:00", "20:00")]);
    await obre("/repartidor/franges", "repartidor");

    expect(horesDelDia(2)).toEqual(["09:00", "13:00", "16:00", "20:00"]);
  });

  it("treu només la franja triada", async () => {
    respon([franja(2, "08:00", "10:00"), franja(2, "11:00", "13:00"), franja(2, "16:00", "20:00")]);
    await obre("/repartidor/franges", "repartidor");
    await dia(2).findAll(".treu")[1].trigger("click");
    await desa();

    expect(enviades()).toEqual([franja(2, "08:00", "10:00"), franja(2, "16:00", "20:00")]);
  });

  it("edita una franja sense tocar les altres", async () => {
    await obre("/repartidor/franges", "repartidor");
    await dia(4).findAll("input")[1].setValue("15:00");
    await desa();

    expect(enviades()).toEqual([franja(0, "09:00", "13:00"), franja(4, "09:00", "15:00")]);
  });

  it("desfer un canvi a mà torna a desactivar el botó de desar", async () => {
    await obre("/repartidor/franges", "repartidor");
    const camp = dia(0).findAll("input")[0];

    await camp.setValue("10:00");
    expect(wrapper.get(".desa").element.disabled).toBe(false);
    await camp.setValue("09:00");
    expect(wrapper.get(".desa").element.disabled).toBe(true);
  });
});

describe("desament de les franges", () => {
  it("consulta i desa a l'endpoint del contracte, sense id", async () => {
    await obre("/repartidor/franges", "repartidor");
    expect(api.get).toHaveBeenCalledExactlyOnceWith(RUTA_API);

    await dia(4).get(".treu").trigger("click");
    await desa();

    expect(api.put).toHaveBeenCalledExactlyOnceWith(RUTA_API, {
      franges: [franja(0, "09:00", "13:00")],
    });
  });

  it("accepta franges adjacents (CP-US14-04)", async () => {
    await obre("/repartidor/franges", "repartidor");
    await afegeix(0, "13:00", "17:00");
    await desa();

    expect(enviades()).toContainEqual(franja(0, "13:00", "17:00"));
    expect(wrapper.find(".avis-correcte").exists()).toBe(true);
  });

  it("pinta l'horari que retorna el servidor, ja ordenat", async () => {
    await obre("/repartidor/franges", "repartidor");
    await afegeix(0, "06:00", "08:00");
    api.put.mockResolvedValue({
      data: {
        franges: [franja(0, "06:00", "08:00"), franja(0, "09:00", "13:00"), franja(4, "09:00", "14:30")],
      },
    });
    await desa();

    expect(horesDelDia(0)).toEqual(["06:00", "08:00", "09:00", "13:00"]);
    expect(wrapper.get(".desa").element.disabled).toBe(true);
  });

  it("envia una llista buida per no estar disponible cap dia (CP-US14-03)", async () => {
    await obre("/repartidor/franges", "repartidor");
    await clica(".treu");
    await clica(".treu");
    await desa();

    expect(enviades()).toEqual([]);
    expect(wrapper.findAll(".dia-buit")).toHaveLength(7);
  });

  it("l'avís de desat desapareix en tornar a editar", async () => {
    await obre("/repartidor/franges", "repartidor");
    await dia(4).get(".treu").trigger("click");
    await desa();
    await dia(0).findAll("input")[0].setValue("10:00");

    expect(wrapper.find(".avis-correcte").exists()).toBe(false);
    expect(wrapper.get(".avis").text()).toBe("Tens canvis sense desar.");
  });
});

describe("errors en desar", () => {
  it.each([
    ["dia", "Tria un dia de la setmana, del 0 (dilluns) al 6 (diumenge)."],
    ["hora_inici", "Escriu l'hora amb el format HH:MM."],
    ["hora_fi", "La franja ha d'acabar després de començar."],
    ["hora_fi", "Aquest camp és obligatori."],
  ])("mostra l'error de %s: %s", async (camp, missatge) => {
    api.put.mockRejectedValue(error400({ 1: { [camp]: [missatge] } }));
    await obre("/repartidor/franges", "repartidor");
    await dia(4).findAll("input")[0].setValue("10:00");
    await desa();

    expect(dia(4).get(".error-franja").text()).toBe(missatge);
  });

  it("la posició és la de l'enviament, no la de la pantalla", async () => {
    await obre("/repartidor/franges", "repartidor");
    // Es veu abans que la de divendres, però s'envia l'última (posició 2).
    await afegeix(1);
    api.put.mockRejectedValue(error400({ 2: { hora_inici: ["Aquest camp és obligatori."] } }));
    await desa();

    expect(dia(1).find(".error-franja").exists()).toBe(true);
    expect(dia(4).find(".error-franja").exists()).toBe(false);
  });

  it("mostra alhora els errors de diverses franges", async () => {
    api.put.mockRejectedValue(
      error400({ 0: { hora_inici: ["Primer error."] }, 1: { hora_fi: ["Segon error."] } }),
    );
    await obre("/repartidor/franges", "repartidor");
    await dia(0).findAll("input")[0].setValue("10:00");
    await desa();

    expect(wrapper.findAll(".error-franja").map((error) => error.text())).toEqual([
      "Primer error.",
      "Segon error.",
    ]);
  });

  it("neteja els errors en corregir i desar", async () => {
    api.put.mockRejectedValueOnce(error400({ 1: { hora_fi: ["Error."] } }));
    await obre("/repartidor/franges", "repartidor");
    await dia(4).findAll("input")[1].setValue("08:00");
    await desa();
    expect(wrapper.find(".error-franja").exists()).toBe(true);

    await dia(4).findAll("input")[1].setValue("15:00");
    await desa();

    expect(wrapper.find(".error-franja").exists()).toBe(false);
    expect(wrapper.find(".avis-correcte").exists()).toBe(true);
  });

  it("un error del servidor no es confon amb un de validació", async () => {
    api.put.mockRejectedValue({ response: { status: 500, data: {} } });
    await obre("/repartidor/franges", "repartidor");
    await dia(4).get(".treu").trigger("click");
    await desa();

    expect(wrapper.get(".avis-error").text()).toBe(
      "No s'han pogut desar les franges. Torna-ho a provar.",
    );
    expect(wrapper.get(".desa").element.disabled).toBe(false);
  });
});

describe("navegació", () => {
  it("s'hi arriba des de l'espai del repartidor", async () => {
    await obre("/repartidor", "repartidor");
    await clica('a[href="/repartidor/franges"]');

    await vi.waitFor(() => expect(wrapper.findAll(".dia")).toHaveLength(7));
  });

  it.each([
    [null, "inici-sessio"],
    ["usuari", "home"],
    ["biblioteca", "home"],
  ])("amb el rol %s no es demana cap franja", async (rol, desti) => {
    await obre("/repartidor/franges", rol);

    expect(router.currentRoute.value.name).toBe(desti);
    expect(api.get).not.toHaveBeenCalledWith(RUTA_API);
  });
});
