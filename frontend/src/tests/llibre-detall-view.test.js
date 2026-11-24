import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSessioStore } from "../stores/sessio.js";
import LlibreDetallView from "../views/LlibreDetallView.vue";

const mocks = vi.hoisted(() => ({
  carregaBiblioteques: vi.fn(),
  apuntaLlistaEspera: vi.fn(),
}));
const route = {
  params: { id: "12" },
  query: {
    titol: "La plaça del Diamant",
    autor: "Mercè Rodoreda",
    portada: "",
    cerca: "Rodoreda",
    pagina: "2",
  },
};

vi.mock("../services/biblioteques.js", () => ({
  llistaBibliotequesAmbEstoc: mocks.carregaBiblioteques,
  apuntaLlistaEspera: mocks.apuntaLlistaEspera,
}));

vi.mock("vue-router", () => ({
  useRoute: () => route,
}));

function muntaDetall({ autenticat = false } = {}) {
  const pinia = createPinia();
  setActivePinia(pinia);
  if (autenticat) {
    useSessioStore().iniciarSessio({ accessToken: "test-token" });
  }

  return mount(LlibreDetallView, {
    global: {
      plugins: [pinia],
      stubs: {
        RouterLink: {
          props: ["to"],
          template: "<a><slot /></a>",
        },
      },
    },
  });
}

describe("detall del llibre i disponibilitat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    route.params.id = "12";
    route.query = {
      titol: "La plaça del Diamant",
      autor: "Mercè Rodoreda",
      portada: "",
      cerca: "Rodoreda",
      pagina: "2",
    };
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [
        {
          id: 3,
          nom: "Biblioteca del Centre",
          carrer: "C/ d'exemple",
          numero_porta: "12",
          exemplars: 2,
          distancia_km: 0.6,
        },
      ],
      ordenada_per_distancia: true,
      missatge: null,
    });
  });

  it("consulta l'estoc i mostra les distàncies només si ve ordenat per proximitat", async () => {
    const wrapper = muntaDetall();
    await vi.waitFor(() =>
      expect(mocks.carregaBiblioteques).toHaveBeenCalledWith(12),
    );
    await flushPromises();

    expect(wrapper.get("h1").text()).toBe("La plaça del Diamant");
    expect(wrapper.text()).toContain("Mercè Rodoreda");
    expect(wrapper.text()).toContain("Biblioteca del Centre");
    expect(wrapper.text()).toContain("2 exemplars disponibles");
    expect(wrapper.get(".distance").text()).toBe("0,6 km");
  });

  it("mostra el missatge per a visitants i oculta les distàncies", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [
        {
          id: 3,
          nom: "Biblioteca del Centre",
          carrer: "C/ d'exemple",
          numero_porta: "12",
          exemplars: 2,
        },
      ],
      ordenada_per_distancia: false,
      missatge: "Registrat per ordenar les biblioteques per distància",
    });
    const wrapper = muntaDetall();
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "Registrat per ordenar les biblioteques per distància",
      ),
    );

    expect(wrapper.find(".distance").exists()).toBe(false);
  });

  it("mostra el missatge per afegir una adreça sense inventar distàncies", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [
        {
          id: 3,
          nom: "Biblioteca del Centre",
          carrer: "C/ d'exemple",
          numero_porta: "12",
          exemplars: 2,
          distancia_km: 0.6,
        },
      ],
      ordenada_per_distancia: false,
      missatge: "Afegeix una adreça per continuar",
    });
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain("Afegeix una adreça per continuar"),
    );

    expect(wrapper.find(".distance").exists()).toBe(false);
  });

  it("mostra el missatge literal quan el llibre no té estoc", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    });
    const wrapper = muntaDetall();
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "Cap biblioteca te aquest llibre en estoc",
      ),
    );

    expect(wrapper.find(".library-list").exists()).toBe(false);
  });

  it("permet apuntar-se a la llista d'espera i interpreta el codi 201", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    });
    mocks.apuntaLlistaEspera.mockResolvedValue({ status: 201, data: {} });
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-panel").exists()).toBe(true),
    );
    await wrapper.get(".waitlist-panel button").trigger("click");

    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "T'has apuntat a la llista d'espera d'aquest llibre.",
      ),
    );
    expect(mocks.apuntaLlistaEspera).toHaveBeenCalledWith(12);
    expect(wrapper.get(".waitlist-panel button").element.disabled).toBe(true);
  });

  it("indica si l'usuari ja era a la llista d'espera", async () => {
    mocks.apuntaLlistaEspera.mockResolvedValue({ status: 200, data: {} });
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-panel").exists()).toBe(true),
    );
    await wrapper.get(".waitlist-panel button").trigger("click");

    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "Ja estaves apuntat a la llista d'espera d'aquest llibre.",
      ),
    );
  });

  it("mostra un error si no es pot apuntar a la llista d'espera", async () => {
    mocks.apuntaLlistaEspera.mockRejectedValue({
      response: { data: { detail: "No s'ha trobat." } },
    });
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-panel").exists()).toBe(true),
    );
    await wrapper.get(".waitlist-panel button").trigger("click");

    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-error").text()).toBe("No s'ha trobat."),
    );
  });

  it("mostra un error i permet tornar a carregar la disponibilitat", async () => {
    mocks.carregaBiblioteques
      .mockRejectedValueOnce(new Error("servidor aturat"))
      .mockResolvedValueOnce({
        biblioteques: [],
        ordenada_per_distancia: false,
        missatge: "Cap biblioteca te aquest llibre en estoc",
      });
    const wrapper = muntaDetall();
    await vi.waitFor(() => expect(wrapper.find(".page-error").exists()).toBe(true));

    await wrapper.get(".page-error button").trigger("click");
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "Cap biblioteca te aquest llibre en estoc",
      ),
    );
    expect(mocks.carregaBiblioteques).toHaveBeenCalledTimes(2);
  });
});
