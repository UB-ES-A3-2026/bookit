import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import router, { nomesRepartidors } from "../router/index.js";
import FrangesView from "../views/FrangesView.vue";

const servei = vi.hoisted(() => ({
  llistaFranges: vi.fn(),
  desaFranges: vi.fn(),
}));

vi.mock("../services/franges.js", () => servei);

let wrapper;
let pinia;

async function renderitza() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p />" } },
      { path: "/pagina", name: "pagina", component: { template: "<p />" } },
      { path: "/repartidor", name: "espai-repartidor", component: { template: "<p />" } },
    ],
  });
  await router.push("/pagina");
  wrapper = mount(FrangesView, { global: { plugins: [pinia, router] } });
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

const horari = [
  { id: 4, dia: 0, hora_inici: "09:00", hora_fi: "13:00" },
  { id: 6, dia: 4, hora_inici: "09:00", hora_fi: "14:30" },
];

const dia = (index) => wrapper.findAll(".dia")[index];

async function desa() {
  await wrapper.get("form").trigger("submit");
  await flushPromises();
}

describe("Franges de disponibilitat", () => {
  beforeEach(() => {
    servei.llistaFranges.mockResolvedValue(horari);
  });

  it("mostra cada franja al seu dia", async () => {
    await renderitza();

    expect(wrapper.findAll(".dia")).toHaveLength(7);
    expect(dia(0).findAll("input").map((camp) => camp.element.value)).toEqual(["09:00", "13:00"]);
    expect(dia(4).findAll("input").map((camp) => camp.element.value)).toEqual(["09:00", "14:30"]);
    expect(dia(6).text()).toContain("No disponible");
    expect(wrapper.get(".desa").element.disabled).toBe(true);
  });

  it("afegeix una franja i envia la setmana sencera, sense id", async () => {
    servei.desaFranges.mockImplementation(async (franges) => franges);
    await renderitza();

    await dia(6).get(".afegeix").trigger("click");
    const [inici, fi] = dia(6).findAll("input");
    await inici.setValue("10:00");
    await fi.setValue("12:00");
    await desa();

    expect(servei.desaFranges).toHaveBeenCalledWith([
      { dia: 0, hora_inici: "09:00", hora_fi: "13:00" },
      { dia: 4, hora_inici: "09:00", hora_fi: "14:30" },
      { dia: 6, hora_inici: "10:00", hora_fi: "12:00" },
    ]);
    expect(wrapper.get(".avis-correcte").text()).toBe("S'han desat les teves franges.");
    expect(wrapper.get(".desa").element.disabled).toBe(true);
  });

  it("permet deixar la setmana sense cap franja", async () => {
    servei.desaFranges.mockResolvedValue([]);
    await renderitza();

    await dia(0).get(".treu").trigger("click");
    await dia(4).get(".treu").trigger("click");
    await desa();

    expect(servei.desaFranges).toHaveBeenCalledWith([]);
    expect(wrapper.findAll(".franja")).toHaveLength(0);
  });

  it("mostra cada error a la franja de la posició que diu l'API", async () => {
    const missatge = "La franja ha d'acabar després de començar.";
    servei.desaFranges.mockRejectedValue({
      response: { status: 400, data: { franges: { 1: { hora_fi: [missatge] } } } },
    });
    await renderitza();

    await dia(4).findAll("input")[1].setValue("08:00");
    await desa();

    expect(dia(4).get(".error-franja").text()).toBe(missatge);
    expect(dia(0).find(".error-franja").exists()).toBe(false);
    expect(dia(4).findAll("input")[1].element.value).toBe("08:00");
  });

  it("mostra el missatge de franges que es trepitgen", async () => {
    const missatge = "Les franges del dilluns de 09:00 a 13:00 i de 12:00 a 14:00 es trepitgen.";
    servei.desaFranges.mockRejectedValue({
      response: { status: 400, data: { franges: [missatge] } },
    });
    await renderitza();

    await dia(0).get(".afegeix").trigger("click");
    await desa();

    expect(wrapper.get(".avis-error").text()).toBe(missatge);
  });

  it("conserva els canvis si no es poden desar", async () => {
    servei.desaFranges.mockRejectedValue(new Error("Network Error"));
    await renderitza();

    await dia(0).get(".treu").trigger("click");
    await desa();

    expect(wrapper.get(".avis-error").text()).toContain("No s'han pogut desar les franges.");
    expect(wrapper.findAll(".franja")).toHaveLength(1);
    expect(wrapper.get(".desa").element.disabled).toBe(false);
  });

  it("bloqueja l'horari mentre es desa", async () => {
    servei.desaFranges.mockReturnValue(new Promise(() => {}));
    await renderitza();

    await dia(0).get(".treu").trigger("click");
    await desa();

    expect(wrapper.get("fieldset").element.disabled).toBe(true);
    expect(wrapper.get(".desa").text()).toBe("Desant...");
  });

  it("mostra que està carregant", async () => {
    servei.llistaFranges.mockReturnValue(new Promise(() => {}));
    await renderitza();

    expect(wrapper.get('[role="status"]').text()).toBe("Carregant les franges...");
  });

  it("si no es poden carregar, no deixa desar i permet tornar-ho a provar", async () => {
    servei.llistaFranges.mockRejectedValueOnce(new Error("Network Error"));
    await renderitza();
    expect(wrapper.find("form").exists()).toBe(false);

    await wrapper.get(".secondary-button").trigger("click");
    await flushPromises();

    expect(wrapper.findAll(".franja")).toHaveLength(2);
  });

  it("torna a l'inici si l'API respon 403", async () => {
    servei.llistaFranges.mockRejectedValue({ response: { status: 403 } });
    const router = await renderitza();

    expect(router.currentRoute.value.name).toBe("home");
  });
});

describe("accés a la ruta", () => {
  it("està protegida", () => {
    expect(router.resolve("/repartidor/franges").matched[0].beforeEnter).toBe(nomesRepartidors);
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
