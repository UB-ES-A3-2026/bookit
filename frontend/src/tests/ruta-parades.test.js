import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import RutaView from "../views/RutaView.vue";

// US13-T5: botons per marcar una parada com a completada o fallida.
const servei = vi.hoisted(() => ({
  llistaRutaAvui: vi.fn(),
  completaParada: vi.fn(),
  fallaParada: vi.fn(),
}));

vi.mock("../services/ruta.js", () => servei);

let wrapper;
let router;

function parada(id, ordre, tipus, extra = {}) {
  return {
    id,
    ordre,
    tipus,
    comanda: 12,
    estat: "preparada",
    estat_parada: "pendent",
    motiu: "",
    llibres: [{ id: 7, titol: "Solitud", autor: "Víctor Català", portada: "" }],
    adreca:
      tipus === "recollida"
        ? { biblioteca: { id: 3, nom: "Biblioteca Central" }, text: null, latitud: null, longitud: null }
        : { biblioteca: null, text: "C/ Major 1", latitud: null, longitud: null },
    ...extra,
  };
}

const ruta = () => [parada(18, 1, "recollida"), parada(19, 2, "lliurament")];

function errorHttp(status, data = {}) {
  return Object.assign(new Error("error"), { response: { status, data } });
}

async function renderitza() {
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/ruta", name: "ruta", component: { template: "<p />" } },
      { path: "/repartidor", name: "espai-repartidor", component: { template: "<p />" } },
    ],
  });
  await router.push("/ruta");
  const pinia = createPinia();
  setActivePinia(pinia);
  wrapper = mount(RutaView, { global: { plugins: [pinia, router] } });
  await flushPromises();
}

const parades = () => wrapper.findAll(".parada");
const boto = (indexParada, text) =>
  parades()[indexParada].findAll("button").find((element) => element.text() === text);

beforeEach(() => {
  vi.resetAllMocks();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

describe("botons de les parades pendents", () => {
  it("mostra els botons Completada i Fallida a cada parada pendent", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    for (const element of parades()) {
      expect(element.find(".boto-completada").exists()).toBe(true);
      expect(element.find(".boto-fallida").exists()).toBe(true);
    }
  });

  it("no mostra botons a les parades completades o fallides i n'ensenya l'estat i el motiu", async () => {
    servei.llistaRutaAvui.mockResolvedValue([
      parada(18, 1, "recollida", { estat_parada: "completada" }),
      parada(19, 2, "lliurament", { estat_parada: "fallida", motiu: "No hi havia ningú." }),
    ]);
    await renderitza();

    expect(wrapper.find(".accions-parada").exists()).toBe(false);
    expect(parades()[0].find(".estat-parada").text()).toBe("Completada");
    expect(parades()[1].find(".estat-parada").text()).toContain("Fallida");
    expect(parades()[1].find(".estat-parada").text()).toContain("No hi havia ningú.");
  });
});

describe("marcar una parada com a completada", () => {
  it("crida l'endpoint, mostra la confirmació i recarrega la ruta", async () => {
    servei.llistaRutaAvui
      .mockResolvedValueOnce(ruta())
      .mockResolvedValueOnce([
        parada(18, 1, "recollida", { estat: "en_cami", estat_parada: "completada" }),
        parada(19, 2, "lliurament", { estat: "en_cami" }),
      ]);
    servei.completaParada.mockResolvedValue({ id: 18, estat: "completada" });
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(servei.completaParada).toHaveBeenCalledWith(18);
    expect(servei.llistaRutaAvui).toHaveBeenCalledTimes(2);
    expect(wrapper.find(".missatge-exit").text()).toBe("Parada 1 marcada com a completada.");
    expect(parades()[0].find(".estat-parada").text()).toBe("Completada");
    expect(parades()[1].find(".boto-completada").exists()).toBe(true);
  });

  it("mostra el missatge del backend si la parada no es pot completar (409)", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.completaParada.mockRejectedValue(
      errorHttp(409, { detail: "Cal recollir la comanda abans de lliurar-la." }),
    );
    await renderitza();

    await boto(1, "Completada").trigger("click");
    await flushPromises();

    expect(parades()[1].find(".error-parada").text()).toBe(
      "Cal recollir la comanda abans de lliurar-la.",
    );
    expect(wrapper.find(".missatge-exit").exists()).toBe(false);
    expect(servei.llistaRutaAvui).toHaveBeenCalledTimes(1);
  });

  it("en fer una altra acció esborra l'error d'una parada anterior", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.completaParada
      .mockRejectedValueOnce(errorHttp(409, { detail: "La comanda no permet completar aquest lliurament." }))
      .mockResolvedValueOnce({ id: 18, estat: "completada" });
    await renderitza();

    await boto(1, "Completada").trigger("click");
    await flushPromises();
    expect(parades()[1].find(".error-parada").exists()).toBe(true);

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(wrapper.find(".error-parada").exists()).toBe(false);
  });

  it("avisa si la parada ja no és a la ruta (404) i torna a carregar-la", async () => {
    servei.llistaRutaAvui.mockResolvedValueOnce(ruta()).mockResolvedValueOnce(ruta());
    servei.completaParada.mockRejectedValue(errorHttp(404));
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(parades()[0].find(".error-parada").text()).toBe(
      "Aquesta parada ja no és a la teva ruta.",
    );
    expect(servei.llistaRutaAvui).toHaveBeenCalledTimes(2);
  });

  it("mostra un error genèric si falla la xarxa", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.completaParada.mockRejectedValue(new Error("Network Error"));
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(parades()[0].find(".error-parada").text()).toBe(
      "No s'ha pogut actualitzar la parada. Torna-ho a provar.",
    );
  });

  it("torna a l'inici si la sessió ja no és de repartidor (403)", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.completaParada.mockRejectedValue(errorHttp(403));
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("marcar una parada com a fallida", () => {
  it("el botó Fallida obre el formulari del motiu i Cancel·lar el tanca", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    expect(parades()[1].find("textarea").exists()).toBe(true);
    expect(parades()[1].find("label").text()).toBe("Motiu de la parada fallida");

    await boto(1, "Cancel·lar").trigger("click");
    expect(parades()[1].find("textarea").exists()).toBe(false);
    expect(servei.fallaParada).not.toHaveBeenCalled();
  });

  it("no envia res si el motiu és buit o només té espais", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await parades()[1].find("textarea").setValue("   ");
    await parades()[1].find("form").trigger("submit");
    await flushPromises();

    expect(servei.fallaParada).not.toHaveBeenCalled();
    expect(parades()[1].find(".error-camp").text()).toBe("Cal indicar el motiu.");
    expect(parades()[1].find("textarea").attributes("aria-invalid")).toBe("true");
  });

  it("envia el motiu sense espais, mostra la confirmació i recarrega la ruta", async () => {
    servei.llistaRutaAvui
      .mockResolvedValueOnce(ruta())
      .mockResolvedValueOnce([parada(18, 1, "recollida", { estat_parada: "completada" })]);
    servei.fallaParada.mockResolvedValue({ id: 19, estat: "fallida" });
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await parades()[1].find("textarea").setValue("  No hi havia ningú al domicili.  ");
    await parades()[1].find("form").trigger("submit");
    await flushPromises();

    expect(servei.fallaParada).toHaveBeenCalledWith(19, "No hi havia ningú al domicili.");
    expect(wrapper.find(".missatge-exit").text()).toBe("Parada 2 marcada com a fallida.");
    expect(wrapper.find("textarea").exists()).toBe(false);
    expect(parades()).toHaveLength(1);
  });

  it("mostra al camp l'error de validació del backend (400)", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockRejectedValue(
      errorHttp(400, { motiu: ["El motiu no pot tenir més de 500 caràcters."] }),
    );
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await parades()[1].find("textarea").setValue("Motiu");
    await parades()[1].find("form").trigger("submit");
    await flushPromises();

    expect(parades()[1].find(".error-camp").text()).toBe(
      "El motiu no pot tenir més de 500 caràcters.",
    );
    expect(parades()[1].find("textarea").exists()).toBe(true);
  });

  it("mostra el missatge del backend si la parada ja està tancada (409)", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockRejectedValue(
      errorHttp(409, { detail: "La parada ja està fallida amb un motiu diferent." }),
    );
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await parades()[1].find("textarea").setValue("Motiu nou");
    await parades()[1].find("form").trigger("submit");
    await flushPromises();

    expect(parades()[1].find(".error-parada").text()).toBe(
      "La parada ja està fallida amb un motiu diferent.",
    );
  });
});
