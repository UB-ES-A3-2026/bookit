import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import NotificacionsCapcalera from "../components/NotificacionsCapcalera.vue";

const servei = vi.hoisted(() => ({
  llistaNotificacions: vi.fn(),
  marcaLlegida: vi.fn(),
  marcaTotesLlegides: vi.fn(),
}));

vi.mock("../services/notificacions.js", () => servei);

const REBUDA = "La teva comanda s'ha rebut correctament. La biblioteca ja l'està preparant";
const PREPARADA = "La teva comanda ja està preparada i aviat sortirà cap a casa teva";

function dades(llegides = [false, false, true]) {
  return llegides.map((llegida, index) => ({
    id: 31 - index,
    comanda: 12,
    text: index === 0 ? PREPARADA : REBUDA,
    llegida,
    creada: "2026-11-17T09:05:00Z",
  }));
}

let wrapper;
let pinia;

async function renderitza(rol = "usuari") {
  if (rol) {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol });
  }
  wrapper = mount(NotificacionsCapcalera, {
    attachTo: document.body,
    global: { plugins: [pinia] },
  });
  await flushPromises();
}

async function clica(selector) {
  await wrapper.get(selector).trigger("click");
  await flushPromises();
}

beforeEach(() => {
  vi.resetAllMocks();
  servei.llistaNotificacions.mockImplementation(async () => dades());
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

describe("notificacions de la capçalera", () => {
  it.each([null, "biblioteca", "repartidor"])("no surt amb el rol %s", async (rol) => {
    await renderitza(rol);

    expect(wrapper.find(".notificacions").exists()).toBe(false);
    expect(servei.llistaNotificacions).not.toHaveBeenCalled();
  });

  it("compta només les noves", async () => {
    await renderitza();

    expect(wrapper.get(".comptador").text()).toBe("2 noves");
  });

  it("no mostra el comptador si totes estan llegides", async () => {
    servei.llistaNotificacions.mockResolvedValue(dades([true, true]));
    await renderitza();

    expect(wrapper.find(".comptador").exists()).toBe(false);
  });

  it("en obrir-la, actualitza la llista i mostra els textos en el mateix ordre", async () => {
    await renderitza();
    expect(wrapper.get(".panell").element.style.display).toBe("none");

    await clica(".notificacions-boto");

    expect(servei.llistaNotificacions).toHaveBeenCalledTimes(2);
    expect(wrapper.get(".notificacions-boto").attributes("aria-expanded")).toBe("true");
    expect(wrapper.get(".panell").element.style.display).toBe("");
    expect(wrapper.findAll(".text").map((text) => text.text())).toEqual([PREPARADA, REBUDA, REBUDA]);
  });

  it("marca una notificació com a llegida", async () => {
    servei.marcaLlegida.mockResolvedValue({});
    await renderitza();
    await clica(".notificacions-boto");
    await clica(".llegeix");

    expect(servei.marcaLlegida).toHaveBeenCalledWith(31);
    expect(wrapper.get(".comptador").text()).toBe("1 nova");
    // El botó clicat desapareix i el panell ha de continuar obert.
    expect(wrapper.get(".notificacions-boto").attributes("aria-expanded")).toBe("true");
  });

  it("marca totes les notificacions i torna a demanar la llista", async () => {
    servei.marcaTotesLlegides.mockResolvedValue({ marcades: 2 });
    await renderitza();
    await clica(".notificacions-boto");
    servei.llistaNotificacions.mockResolvedValue(dades([true, true, true]));
    await clica(".llegeix-totes");

    expect(servei.marcaTotesLlegides).toHaveBeenCalledOnce();
    expect(wrapper.find(".comptador").exists()).toBe(false);
  });

  it("no dona per llegida una notificació si el desament falla", async () => {
    servei.marcaLlegida.mockRejectedValue(new Error("Network Error"));
    await renderitza();
    await clica(".notificacions-boto");
    await clica(".llegeix");

    expect(wrapper.get(".error-accio").text()).toContain("No s'ha pogut desar la lectura.");
    expect(wrapper.get(".comptador").text()).toBe("2 noves");
  });

  it("una càrrega antiga que arriba tard no desfà una lectura", async () => {
    servei.marcaLlegida.mockResolvedValue({});
    await renderitza();
    let respon;
    servei.llistaNotificacions.mockReturnValue(new Promise((resol) => (respon = resol)));
    await clica(".notificacions-boto");
    await clica(".llegeix");
    respon(dades());
    await flushPromises();

    expect(wrapper.get(".comptador").text()).toBe("1 nova");
  });

  it("avisa quan no n'hi ha cap", async () => {
    servei.llistaNotificacions.mockResolvedValue([]);
    await renderitza();

    expect(wrapper.get(".buit").text()).toBe("No tens cap notificació.");
  });

  it("mostra l'error de càrrega i permet tornar-ho a provar", async () => {
    servei.llistaNotificacions.mockRejectedValueOnce(new Error("Network Error"));
    await renderitza();
    expect(wrapper.get(".error-carrega").text()).toContain("No s'han pogut carregar");

    await clica(".reintenta");

    expect(wrapper.find(".error-carrega").exists()).toBe(false);
    expect(wrapper.findAll(".notificacio")).toHaveLength(3);
  });

  it("es tanca amb Escapada i en clicar a fora", async () => {
    await renderitza();
    const boto = wrapper.get(".notificacions-boto");

    await clica(".notificacions-boto");
    await boto.trigger("keydown", { key: "Escape" });
    expect(boto.attributes("aria-expanded")).toBe("false");

    await clica(".notificacions-boto");
    document.body.click();
    await flushPromises();
    expect(boto.attributes("aria-expanded")).toBe("false");
  });

  it("descarta les dades en tancar la sessió", async () => {
    let respon;
    servei.llistaNotificacions.mockReturnValueOnce(new Promise((resol) => (respon = resol)));
    await renderitza();

    useSessioStore().tancarSessio();
    await flushPromises();
    respon(dades());
    await flushPromises();
    expect(wrapper.find(".notificacions").exists()).toBe(false);

    servei.llistaNotificacions.mockResolvedValue([]);
    useSessioStore().iniciarSessio({ accessToken: "un-altre-token", rol: "usuari" });
    await flushPromises();
    expect(wrapper.findAll(".notificacio")).toHaveLength(0);
  });
});
