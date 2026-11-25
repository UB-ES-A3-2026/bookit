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
// La mateixa comanda, amb la recollida ja feta: el lliurament ja es pot completar.
const rutaRecollida = () => [
  parada(18, 1, "recollida", { estat: "en_cami", estat_parada: "completada" }),
  parada(19, 2, "lliurament", { estat: "en_cami" }),
];

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

describe("lliurament abans de la recollida", () => {
  it("no deixa completar el lliurament mentre la recollida està pendent i ho explica", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    expect(parades()[1].find(".boto-completada").attributes("disabled")).toBeDefined();
    expect(parades()[1].find(".avis-recollida").text()).toBe(
      "Primer marca la recollida d'aquesta comanda a la biblioteca.",
    );
    expect(parades()[0].find(".boto-completada").attributes("disabled")).toBeUndefined();
    expect(parades()[0].find(".avis-recollida").exists()).toBe(false);

    await parades()[1].find(".boto-completada").trigger("click");
    expect(servei.completaParada).not.toHaveBeenCalled();
  });

  it("el lliurament es pot marcar com a fallit encara que no s'hagi recollit", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    expect(parades()[1].find(".boto-fallida").attributes("disabled")).toBeUndefined();
  });

  it("un cop recollida, el lliurament es pot completar", async () => {
    servei.llistaRutaAvui.mockResolvedValueOnce(ruta()).mockResolvedValueOnce(rutaRecollida());
    servei.completaParada.mockResolvedValue({ id: 18, estat: "completada" });
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(parades()[1].find(".boto-completada").attributes("disabled")).toBeUndefined();
    expect(parades()[1].find(".avis-recollida").exists()).toBe(false);
  });

  it("la recollida pendent d'una altra comanda no bloqueja el lliurament", async () => {
    servei.llistaRutaAvui.mockResolvedValue([
      parada(18, 1, "recollida", { estat: "en_cami", estat_parada: "completada" }),
      parada(20, 2, "recollida", { comanda: 13 }),
      parada(19, 3, "lliurament", { estat: "en_cami" }),
    ]);
    await renderitza();

    expect(parades()[2].find(".boto-completada").attributes("disabled")).toBeUndefined();
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
    servei.llistaRutaAvui.mockResolvedValue(rutaRecollida());
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
    // Dues recollides de comandes diferents.
    servei.llistaRutaAvui.mockResolvedValue([
      parada(18, 1, "recollida"),
      parada(20, 2, "recollida", { comanda: 13 }),
    ]);
    servei.completaParada
      .mockRejectedValueOnce(errorHttp(409, { detail: "La comanda no permet completar aquest lliurament." }))
      .mockResolvedValueOnce({ id: 20, estat: "completada" });
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();
    expect(parades()[0].find(".error-parada").exists()).toBe(true);

    await boto(1, "Completada").trigger("click");
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

// US13-T6: casos addicionals dels botons i del motiu obligatori.

function promesaPendent() {
  let resol;
  const promesa = new Promise((resolve) => {
    resol = resolve;
  });
  return { promesa, resol };
}

async function obreIFormulari(indexParada, text) {
  await boto(indexParada, "Fallida").trigger("click");
  await parades()[indexParada].find("textarea").setValue(text);
  await parades()[indexParada].find("form").trigger("submit");
  await flushPromises();
}

describe("estat de cada parada", () => {
  it("els botons indiquen el número de parada per als lectors de pantalla", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    expect(parades()[1].find(".boto-completada").attributes("aria-label")).toBe(
      "Marcar la parada 2 com a completada",
    );
    expect(parades()[1].find(".boto-fallida").attributes("aria-label")).toBe(
      "Marcar la parada 2 com a fallida",
    );
  });

  it("tracta com a pendent una parada sense estat_parada", async () => {
    const sensEstat = parada(18, 1, "recollida");
    delete sensEstat.estat_parada;
    servei.llistaRutaAvui.mockResolvedValue([sensEstat]);
    await renderitza();

    expect(parades()[0].find(".boto-completada").exists()).toBe(true);
  });

  it("mostra una parada cancel·lada sense botons ni motiu", async () => {
    servei.llistaRutaAvui.mockResolvedValue([
      parada(18, 1, "recollida", { estat_parada: "cancellada" }),
      parada(19, 2, "lliurament"),
    ]);
    await renderitza();

    expect(parades()[0].find(".accions-parada").exists()).toBe(false);
    expect(parades()[0].find(".estat-parada").text()).toBe("Cancel·lada");
    expect(parades()[0].find(".motiu").exists()).toBe(false);
    expect(parades()[1].find(".accions-parada").exists()).toBe(true);
  });
});

describe("mentre s'envia una acció", () => {
  it("desactiva tots els botons i no permet enviar dues vegades", async () => {
    const pendent = promesaPendent();
    servei.llistaRutaAvui.mockResolvedValueOnce(ruta()).mockResolvedValueOnce(rutaRecollida());
    servei.completaParada.mockReturnValue(pendent.promesa);
    await renderitza();

    await boto(0, "Completada").trigger("click");

    expect(parades()[0].find(".boto-completada").text()).toBe("Desant...");
    for (const element of wrapper.findAll(".accions-parada button")) {
      expect(element.attributes("disabled")).toBeDefined();
    }
    await parades()[0].find(".boto-completada").trigger("click");
    expect(servei.completaParada).toHaveBeenCalledTimes(1);

    pendent.resol({ id: 18, estat: "completada" });
    await flushPromises();

    for (const element of wrapper.findAll(".accions-parada button")) {
      expect(element.attributes("disabled")).toBeUndefined();
    }
  });

  it("desactiva Confirmar i Cancel·lar mentre s'envia la fallida", async () => {
    const pendent = promesaPendent();
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockReturnValue(pendent.promesa);
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await parades()[1].find("textarea").setValue("Biblioteca tancada");
    await parades()[1].find("form").trigger("submit");

    const botons = parades()[1].findAll("form button");
    expect(botons[0].text()).toBe("Desant...");
    for (const element of botons) {
      expect(element.attributes("disabled")).toBeDefined();
    }

    pendent.resol({ id: 19, estat: "fallida" });
    await flushPromises();
  });
});

describe("motiu obligatori de la parada fallida", () => {
  it("el camp és obligatori, té una etiqueta i limita la longitud a 500", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    const camp = parades()[1].find("textarea");

    expect(camp.attributes("required")).toBeDefined();
    expect(camp.attributes("maxlength")).toBe("500");
    expect(parades()[1].find(`label[for="${camp.attributes("id")}"]`).exists()).toBe(true);
    expect(camp.attributes("aria-invalid")).toBe("false");
  });

  it("no envia un motiu buit i relaciona l'error amb el camp", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await obreIFormulari(1, "");

    const camp = parades()[1].find("textarea");
    const error = parades()[1].find(".error-camp");
    expect(servei.fallaParada).not.toHaveBeenCalled();
    expect(error.text()).toBe("Cal indicar el motiu.");
    expect(camp.attributes("aria-describedby")).toBe(error.attributes("id"));
  });

  it("no envia un motiu de més de 500 caràcters", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await obreIFormulari(1, "a".repeat(501));

    expect(servei.fallaParada).not.toHaveBeenCalled();
    expect(parades()[1].find(".error-camp").text()).toBe(
      "El motiu no pot tenir més de 500 caràcters.",
    );
  });

  it("accepta un motiu d'exactament 500 caràcters", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockResolvedValue({ id: 19, estat: "fallida" });
    await renderitza();

    await obreIFormulari(1, "a".repeat(500));

    expect(servei.fallaParada).toHaveBeenCalledWith(19, "a".repeat(500));
  });

  it("després d'un motiu buit, un motiu vàlid s'envia i tanca el formulari", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockResolvedValue({ id: 19, estat: "fallida" });
    await renderitza();

    await obreIFormulari(1, "  ");
    await parades()[1].find("textarea").setValue("Biblioteca tancada");
    await parades()[1].find("form").trigger("submit");
    await flushPromises();

    expect(servei.fallaParada).toHaveBeenCalledWith(19, "Biblioteca tancada");
    expect(wrapper.find("textarea").exists()).toBe(false);
    expect(wrapper.find(".error-camp").exists()).toBe(false);
  });

  it("en cancel·lar i tornar a obrir, el motiu i l'error comencen buits", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await obreIFormulari(1, "");
    await parades()[1].find("textarea").setValue("Text a mig escriure");
    await boto(1, "Cancel·lar").trigger("click");
    await boto(1, "Fallida").trigger("click");

    expect(parades()[1].find("textarea").element.value).toBe("");
    expect(parades()[1].find(".error-camp").exists()).toBe(false);
  });

  it("només hi ha un formulari obert alhora", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    await renderitza();

    await boto(1, "Fallida").trigger("click");
    await boto(0, "Fallida").trigger("click");

    expect(wrapper.findAll("textarea")).toHaveLength(1);
    expect(parades()[0].find("textarea").exists()).toBe(true);
    expect(parades()[1].find(".boto-completada").exists()).toBe(true);
  });

  it("si la xarxa falla, manté el formulari obert amb el motiu i mostra l'error", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockRejectedValue(new Error("Network Error"));
    await renderitza();

    await obreIFormulari(1, "Biblioteca tancada");

    expect(parades()[1].find("textarea").element.value).toBe("Biblioteca tancada");
    expect(parades()[1].find(".error-parada").text()).toBe(
      "No s'ha pogut actualitzar la parada. Torna-ho a provar.",
    );
  });

  it("torna a l'inici si la sessió ha caducat (401)", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.fallaParada.mockRejectedValue(errorHttp(401));
    await renderitza();

    await obreIFormulari(1, "Biblioteca tancada");

    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("missatges després de les accions", () => {
  it("si la recàrrega falla després de completar, manté la llista i la confirmació", async () => {
    servei.llistaRutaAvui
      .mockResolvedValueOnce(ruta())
      .mockRejectedValueOnce(new Error("Network Error"));
    servei.completaParada.mockResolvedValue({ id: 18, estat: "completada" });
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();

    expect(parades()).toHaveLength(2);
    expect(wrapper.find(".missatge-exit").text()).toBe("Parada 1 marcada com a completada.");
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it("la confirmació anterior desapareix en obrir el formulari de fallida", async () => {
    servei.llistaRutaAvui.mockResolvedValue(ruta());
    servei.completaParada.mockResolvedValue({ id: 18, estat: "completada" });
    await renderitza();

    await boto(0, "Completada").trigger("click");
    await flushPromises();
    expect(wrapper.find(".missatge-exit").exists()).toBe(true);

    await boto(1, "Fallida").trigger("click");

    expect(wrapper.find(".missatge-exit").exists()).toBe(false);
  });
});
