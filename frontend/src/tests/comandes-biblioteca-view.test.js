import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesBiblioteques } from "../router/index.js";
import ComandesBibliotecaView from "../views/ComandesBibliotecaView.vue";

const servei = vi.hoisted(() => ({
  llistaComandesBiblioteca: vi.fn(),
  marcaComandaPreparada: vi.fn(),
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

  it("una comanda de recollida diu que es recull a la biblioteca en lloc de la data", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue([
      { ...comanda(12, "preparada", null), tipus_lliurament: "recollida" },
      { ...comanda(4, "preparada", null), tipus_lliurament: "domicili" },
    ]);
    await renderitza();

    const dates = wrapper.findAll(".data-lliurament").map((data) => data.text());
    expect(dates).toEqual(["Recollida a la biblioteca", "Sense data"]);
  });
});

describe("Llesta per a recollida", () => {
  const TEXT_BOTO = "Llesta per a recollida";

  function botons() {
    return wrapper.findAll("button").filter((boto) => boto.text() === TEXT_BOTO);
  }

  function targeta(id) {
    return wrapper.findAll(".comanda").find((element) => element.get("h2").text() === `Comanda ${id}`);
  }

  // Resposta del POST: la comanda amb el format de Comanda, que no porta l'usuari.
  function resposta(id, canvis = {}) {
    const { usuari: _usuari, ...sensUsuari } = comanda(id, "preparada", "2026-11-20");
    return { ...sensUsuari, ...canvis };
  }

  function deferida() {
    let resol;
    const promesa = new Promise((r) => {
      resol = r;
    });
    return { promesa, resol };
  }

  it("només surt a les comandes rebudes", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    await renderitza();

    expect(botons()).toHaveLength(1);
    expect(targeta(12).text()).toContain(TEXT_BOTO);
    expect(targeta(4).text()).not.toContain(TEXT_BOTO);
    expect(targeta(8).text()).not.toContain(TEXT_BOTO);
  });

  it("marca la comanda i actualitza la llista sense tornar-la a demanar", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockResolvedValue(resposta(12));
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(servei.marcaComandaPreparada).toHaveBeenCalledTimes(1);
    expect(servei.marcaComandaPreparada).toHaveBeenCalledWith(12);
    expect(targeta(12).get(".etiqueta").text()).toBe("Preparada");
    expect(botons()).toHaveLength(0);
    // Es conserva l'usuari, que la resposta no porta, i no es torna a carregar la llista.
    expect(targeta(12).text()).toContain("Anna Puig");
    expect(servei.llistaComandesBiblioteca).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  });

  it("agafa la data de lliurament de la resposta", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue([comanda(12, "rebuda", null)]);
    servei.marcaComandaPreparada.mockResolvedValue(resposta(12, { data_lliurament: "2026-11-25" }));
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get(".data-lliurament").text()).toBe("25/11/2026");
  });

  it("només toca la comanda marcada", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue([
      comanda(12, "rebuda", "2026-11-20"),
      comanda(13, "rebuda", "2026-11-21"),
    ]);
    servei.marcaComandaPreparada.mockResolvedValue(resposta(13));
    await renderitza();

    await botons()[1].trigger("click");
    await flushPromises();

    expect(servei.marcaComandaPreparada).toHaveBeenCalledWith(13);
    expect(targeta(12).get(".etiqueta").text()).toBe("Rebuda");
    expect(targeta(13).get(".etiqueta").text()).toBe("Preparada");
    expect(botons()).toHaveLength(1);
  });

  it("mentre s'envia, mostra que està marcant i no deixa enviar-ne cap altra", async () => {
    const peticio = deferida();
    servei.llistaComandesBiblioteca.mockResolvedValue([
      comanda(12, "rebuda", "2026-11-20"),
      comanda(13, "rebuda", "2026-11-21"),
    ]);
    servei.marcaComandaPreparada.mockReturnValue(peticio.promesa);
    await renderitza();

    await targeta(12).get("button").trigger("click");

    expect(targeta(12).get("button").text()).toBe("Marcant...");
    expect(targeta(12).get("button").attributes("disabled")).toBeDefined();
    expect(targeta(13).get("button").attributes("disabled")).toBeDefined();

    await targeta(13).get("button").trigger("click");
    expect(servei.marcaComandaPreparada).toHaveBeenCalledTimes(1);

    peticio.resol(resposta(12));
    await flushPromises();
    expect(targeta(13).get("button").attributes("disabled")).toBeUndefined();
    expect(targeta(13).get("button").text()).toBe(TEXT_BOTO);
  });

  it("un doble clic ràpid només envia una petició", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockResolvedValue(resposta(12));
    await renderitza();

    // Els dos clics arriben abans que Vue torni a pintar el botó desactivat.
    const boto = botons()[0];
    boto.trigger("click");
    boto.trigger("click");
    await flushPromises();

    expect(servei.marcaComandaPreparada).toHaveBeenCalledTimes(1);
  });

  it("amb un 409 mostra el missatge de l'API i refresca la llista", async () => {
    servei.llistaComandesBiblioteca
      .mockResolvedValueOnce(comandes)
      .mockResolvedValueOnce([comanda(12, "preparada", "2026-11-20"), ...comandes.slice(1)]);
    servei.marcaComandaPreparada.mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "Aquesta comanda ja està llesta per a recollida." },
      },
    });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get('[role="alert"]').text()).toBe(
      "Aquesta comanda ja està llesta per a recollida.",
    );
    expect(servei.llistaComandesBiblioteca).toHaveBeenCalledTimes(2);
    expect(targeta(12).get(".etiqueta").text()).toBe("Preparada");
    expect(botons()).toHaveLength(0);
    // El refresc no amaga la llista amb el missatge de càrrega.
    expect(wrapper.find('[role="status"]').exists()).toBe(false);
  });

  it("amb un 409 per un altre estat mostra el seu missatge", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockRejectedValue({
      response: {
        status: 409,
        data: {
          detail: "Aquesta comanda no es pot marcar com a llesta perquè està cancel·lada.",
        },
      },
    });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get('[role="alert"]').text()).toBe(
      "Aquesta comanda no es pot marcar com a llesta perquè està cancel·lada.",
    );
  });

  it("amb un 409 sense missatge en mostra un de genèric", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockRejectedValue({ response: { status: 409, data: {} } });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get('[role="alert"]').text()).toBe(
      "Aquesta comanda ja no es pot marcar com a llesta.",
    );
  });

  it("amb un 404 avisa que ja no existeix i refresca la llista", async () => {
    servei.llistaComandesBiblioteca
      .mockResolvedValueOnce(comandes)
      .mockResolvedValueOnce(comandes.slice(1));
    servei.marcaComandaPreparada.mockRejectedValue({ response: { status: 404 } });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(servei.llistaComandesBiblioteca).toHaveBeenCalledTimes(2);
    expect(targeta(12)).toBeUndefined();
    expect(wrapper.findAll(".comanda")).toHaveLength(2);
  });

  it("amb un 404 manté l'avís si la comanda encara surt a la llista", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockRejectedValue({ response: { status: 404 } });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get('[role="alert"]').text()).toBe("Aquesta comanda ja no existeix.");
  });

  it("si falla el refresc, es manté la llista que hi havia", async () => {
    servei.llistaComandesBiblioteca
      .mockResolvedValueOnce(comandes)
      .mockRejectedValueOnce(new Error("Network Error"));
    servei.marcaComandaPreparada.mockRejectedValue({
      response: { status: 409, data: { detail: "Aquesta comanda ja està llesta per a recollida." } },
    });
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(wrapper.findAll(".comanda")).toHaveLength(comandes.length);
    expect(wrapper.text()).not.toContain("No s'han pogut carregar les comandes.");
    expect(targeta(12).get('[role="alert"]').text()).toBe(
      "Aquesta comanda ja està llesta per a recollida.",
    );
  });

  it("amb un error de xarxa avisa, no refresca i deixa tornar-ho a provar", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada
      .mockRejectedValueOnce(new Error("Network Error"))
      .mockResolvedValueOnce(resposta(12));
    await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get('[role="alert"]').text()).toBe(
      "No s'ha pogut marcar la comanda com a llesta. Torna-ho a provar més tard.",
    );
    expect(servei.llistaComandesBiblioteca).toHaveBeenCalledTimes(1);
    expect(targeta(12).get(".etiqueta").text()).toBe("Rebuda");

    await botons()[0].trigger("click");
    await flushPromises();

    expect(targeta(12).get(".etiqueta").text()).toBe("Preparada");
    expect(targeta(12).find('[role="alert"]').exists()).toBe(false);
  });

  it("l'error d'una comanda no surt a les altres", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue([
      comanda(12, "rebuda", "2026-11-20"),
      comanda(13, "rebuda", "2026-11-21"),
    ]);
    servei.marcaComandaPreparada.mockRejectedValue(new Error("Network Error"));
    await renderitza();

    await targeta(12).get("button").trigger("click");
    await flushPromises();

    expect(targeta(12).find('[role="alert"]').exists()).toBe(true);
    expect(targeta(13).find('[role="alert"]').exists()).toBe(false);
  });

  it("amb un 403 torna a l'inici", async () => {
    servei.llistaComandesBiblioteca.mockResolvedValue(comandes);
    servei.marcaComandaPreparada.mockRejectedValue({ response: { status: 403 } });
    const router = await renderitza();

    await botons()[0].trigger("click");
    await flushPromises();

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
