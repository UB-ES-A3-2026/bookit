import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.vue";
import router from "../router/index.js";
import { useSessioStore } from "../stores/sessio.js";

// Vistes, router i serveis de veritat: només se simula el client HTTP.
const api = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
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

// La cerca fa servir axios directament.
vi.mock("axios", () => ({
  default: { get: vi.fn(async () => ({ data: { count: 0, results: [] } })) },
}));

const COMANDES = "/prestecs/comandes/";
const NOTIFICACIONS = "/prestecs/notificacions/";

// Literals dels criteris d'acceptació de la US8.
const TEXTOS = [
  "La teva comanda s'ha lliurat correctament. Gaudeix del teu llibre!",
  "En/Na Jordi ja porta la teva comanda. Està en camí!",
  "La teva comanda ja està preparada i aviat sortirà cap a casa teva",
  "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant",
];

let comandes;
let notificacions;

function comanda(id, estat, canvis = {}) {
  return {
    id,
    estat,
    data_lliurament: null,
    biblioteca: { id: 3, nom: "Biblioteca Montbau" },
    llibres: [{ id: 9, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    creada: "2026-11-16T12:20:00Z",
    ...canvis,
  };
}

beforeEach(() => {
  comandes = [];
  notificacions = TEXTOS.map((text, index) => ({
    id: 40 - index,
    comanda: 12,
    text,
    llegida: false,
    creada: "2026-11-17T09:05:00Z",
  }));
  api.get.mockImplementation(async (url) => {
    if (url === COMANDES) return { data: structuredClone(comandes) };
    if (url === NOTIFICACIONS) return { data: structuredClone(notificacions) };
    throw new Error(`Ruta inesperada: ${url}`);
  });
});

describe("les meves comandes", () => {
  it("s'hi arriba des de l'inici i es demanen a l'API", async () => {
    comandes = [comanda(12, "rebuda")];
    await obre("/", "usuari");
    await clica('a[href="/comandes"]');

    await vi.waitFor(() => expect(wrapper.find(".comanda").exists()).toBe(true));
    expect(api.get).toHaveBeenCalledWith(COMANDES);
  });

  it("manté l'ordre de l'API, de la més nova a la més antiga", async () => {
    comandes = [comanda(5, "rebuda"), comanda(30, "lliurada"), comanda(11, "en_cami")];
    await obre("/comandes", "usuari");

    expect(wrapper.findAll(".comanda h2").map((titol) => titol.text())).toEqual([
      "Comanda 5",
      "Comanda 30",
      "Comanda 11",
    ]);
  });

  it.each([
    ["rebuda", "Rebuda"],
    ["preparada", "Preparada"],
    ["en_cami", "En camí"],
    ["lliurada", "Lliurada"],
    ["cancellada", "Cancel·lada"],
  ])("l'estat %s es llegeix %s", async (estat, text) => {
    comandes = [comanda(12, estat)];
    await obre("/comandes", "usuari");

    expect(wrapper.get(".etiqueta").text()).toBe(text);
  });

  it("segueix el recorregut de la comanda en tornar a entrar", async () => {
    comandes = [comanda(12, "rebuda")];
    await obre("/comandes", "usuari");
    expect(wrapper.get(".etiqueta").text()).toBe("Rebuda");

    for (const [estat, text] of [
      ["preparada", "Preparada"],
      ["en_cami", "En camí"],
      ["lliurada", "Lliurada"],
    ]) {
      await router.push("/");
      await flushPromises();
      comandes = [comanda(12, estat)];
      await router.push("/comandes");
      await flushPromises();
      expect(wrapper.get(".etiqueta").text()).toBe(text);
    }
  });

  it("la data prevista no canvia de dia amb el fus horari", async () => {
    vi.stubEnv("TZ", "America/Los_Angeles");
    comandes = [comanda(12, "en_cami", { data_lliurament: "2026-11-20" })];
    await obre("/comandes", "usuari");

    expect(wrapper.get(".data-lliurament").text()).toBe("20/11/2026");
  });

  it.each([
    [null, "inici-sessio"],
    ["biblioteca", "home"],
    ["repartidor", "home"],
  ])("amb el rol %s no es demana cap comanda", async (rol, desti) => {
    await obre("/comandes", rol);

    expect(router.currentRoute.value.name).toBe(desti);
    expect(api.get).not.toHaveBeenCalledWith(COMANDES);
  });
});

describe("notificacions", () => {
  it.each(["/", "/cerca"])("són a la capçalera de %s", async (ruta) => {
    await obre(ruta, "usuari");

    expect(wrapper.get("header .comptador").text()).toBe("4 noves");
  });

  it("mostra els quatre textos literals, de la més nova a la més antiga", async () => {
    await obre("/", "usuari");
    await clica(".notificacions-boto");

    expect(wrapper.findAll(".notificacio .text").map((text) => text.text())).toEqual(TEXTOS);
  });

  it("en marcar-ne una fa el POST d'aquella i no toca les altres", async () => {
    api.post.mockResolvedValue({ data: {} });
    await obre("/", "usuari");
    await clica(".notificacions-boto");
    await wrapper.findAll(".llegeix")[1].trigger("click");
    await flushPromises();

    expect(api.post).toHaveBeenCalledExactlyOnceWith("/prestecs/notificacions/39/llegida/");
    expect(wrapper.findAll(".notificacio").map((fila) => fila.classes("nova"))).toEqual([
      true,
      false,
      true,
      true,
    ]);
  });

  it("en marcar-les totes fa un sol POST", async () => {
    api.post.mockImplementation(async () => {
      notificacions.forEach((notificacio) => (notificacio.llegida = true));
      return { data: { marcades: 4 } };
    });
    await obre("/", "usuari");
    await clica(".notificacions-boto");
    await clica(".llegeix-totes");

    expect(api.post).toHaveBeenCalledExactlyOnceWith("/prestecs/notificacions/llegides/");
    expect(wrapper.find(".comptador").exists()).toBe(false);
  });

  it("si falla marcar-les totes, continuen com a noves", async () => {
    api.post.mockRejectedValue({ response: { status: 500 } });
    await obre("/", "usuari");
    await clica(".notificacions-boto");
    await clica(".llegeix-totes");

    expect(wrapper.get(".error-accio").text()).toContain("No s'ha pogut desar la lectura.");
    expect(wrapper.get(".comptador").text()).toBe("4 noves");
  });

  it("no deixa enviar dues lectures alhora", async () => {
    api.post.mockReturnValue(new Promise(() => {}));
    await obre("/", "usuari");
    await clica(".notificacions-boto");
    await clica(".llegeix");

    const botons = wrapper.findAll(".llegeix, .llegeix-totes");
    expect(botons.every((boto) => boto.element.disabled)).toBe(true);
  });

  it("en obrir el panell hi surt una notificació acabada d'arribar", async () => {
    const totes = notificacions;
    notificacions = totes.slice(1);
    await obre("/", "usuari");
    expect(wrapper.get(".comptador").text()).toBe("3 noves");

    notificacions = totes;
    await clica(".notificacions-boto");

    expect(wrapper.get(".comptador").text()).toBe("4 noves");
    expect(wrapper.get(".notificacio .text").text()).toBe(TEXTOS[0]);
  });

  it("si falla l'actualització, conserva la llista que ja tenia", async () => {
    await obre("/", "usuari");
    api.get.mockRejectedValue({ response: { status: 500 } });
    await clica(".notificacions-boto");

    expect(wrapper.find(".error-carrega").exists()).toBe(true);
    expect(wrapper.findAll(".notificacio")).toHaveLength(4);
  });

  it("desapareixen en tancar la sessió des de l'inici", async () => {
    await obre("/", "usuari");
    await clica(".logout-button");

    expect(wrapper.find(".notificacions").exists()).toBe(false);
    expect(wrapper.text()).not.toContain(TEXTOS[0]);
  });

  it.each([null, "biblioteca", "repartidor"])("amb el rol %s no es demanen", async (rol) => {
    await obre("/", rol);

    expect(wrapper.find(".notificacions").exists()).toBe(false);
    expect(api.get).not.toHaveBeenCalledWith(NOTIFICACIONS);
  });
});
