import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useComandaStore } from "../stores/comanda.js";
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

const push = vi.hoisted(() => vi.fn());

vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => ({ push }),
}));

function muntaDetall({ autenticat = false, rol = "usuari" } = {}) {
  const pinia = createPinia();
  setActivePinia(pinia);
  if (autenticat) {
    useSessioStore().iniciarSessio({ accessToken: "test-token", usuari: { id: 25 }, rol });
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
    vi.resetAllMocks();
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
    expect(wrapper.find(".waitlist-panel").exists()).toBe(false);
  });

  it("mostra totes les biblioteques en l'ordre i amb l'estoc retornats", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [
        {
          id: 8,
          nom: "Biblioteca Propera",
          carrer: "C/ Proper",
          numero_porta: "1",
          exemplars: 1,
          distancia_km: 0.6,
        },
        {
          id: 9,
          nom: "Biblioteca Llunyana",
          carrer: "C/ Llunyà",
          numero_porta: "2",
          exemplars: 4,
          distancia_km: 85.1,
        },
      ],
      ordenada_per_distancia: true,
      missatge: null,
    });
    const wrapper = muntaDetall();
    await vi.waitFor(() =>
      expect(wrapper.findAll(".library-card")).toHaveLength(2),
    );

    const targetes = wrapper.findAll(".library-card");
    expect(targetes[0].text()).toContain("Biblioteca Propera");
    expect(targetes[0].text()).toContain("1 exemplar disponible");
    expect(targetes[1].text()).toContain("Biblioteca Llunyana");
    expect(targetes[1].text()).toContain("4 exemplars disponibles");
    expect(wrapper.findAll(".distance").map((distancia) => distancia.text())).toEqual([
      "0,6 km",
      "85,1 km",
    ]);
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
    expect(wrapper.find(".waitlist-panel").exists()).toBe(true);
    expect(wrapper.get(".waitlist-panel .primary-button").text()).toBe(
      "Inicia sessió",
    );
    expect(mocks.apuntaLlistaEspera).not.toHaveBeenCalled();
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

  it("evita peticions duplicades mentre espera la resposta", async () => {
    let resolResolucio;
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    });
    mocks.apuntaLlistaEspera.mockReturnValue(
      new Promise((resolve) => {
        resolResolucio = resolve;
      }),
    );
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-panel").exists()).toBe(true),
    );
    const boto = wrapper.get(".waitlist-panel button");

    await boto.trigger("click");
    expect(boto.text()).toBe("Apuntant...");
    expect(boto.element.disabled).toBe(true);
    await boto.trigger("click");
    expect(mocks.apuntaLlistaEspera).toHaveBeenCalledTimes(1);

    resolResolucio({ status: 201, data: {} });
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "T'has apuntat a la llista d'espera d'aquest llibre.",
      ),
    );
  });

  it("indica si l'usuari ja era a la llista d'espera", async () => {
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    });
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
    mocks.carregaBiblioteques.mockResolvedValue({
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    });
    mocks.apuntaLlistaEspera.mockRejectedValueOnce({
      response: { data: { detail: "No s'ha trobat." } },
    }).mockResolvedValueOnce({ status: 201, data: {} });
    const wrapper = muntaDetall({ autenticat: true });
    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-panel").exists()).toBe(true),
    );
    await wrapper.get(".waitlist-panel button").trigger("click");

    await vi.waitFor(() =>
      expect(wrapper.find(".waitlist-error").text()).toBe("No s'ha trobat."),
    );
    expect(wrapper.get(".waitlist-panel button").element.disabled).toBe(false);

    await wrapper.get(".waitlist-panel button").trigger("click");
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain(
        "T'has apuntat a la llista d'espera d'aquest llibre.",
      ),
    );
    expect(mocks.apuntaLlistaEspera).toHaveBeenCalledTimes(2);
  });

  it("no consulta l'API si l'identificador del llibre no és vàlid", async () => {
    route.params.id = "id-invalid";
    const wrapper = muntaDetall();
    await vi.waitFor(() => expect(wrapper.find(".page-error").exists()).toBe(true));

    expect(wrapper.text()).toContain("No s'ha pogut trobar aquest llibre.");
    expect(mocks.carregaBiblioteques).not.toHaveBeenCalled();
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

  describe("afegir el llibre a la comanda", () => {
    const CENTRE = { id: 3, nom: "Biblioteca del Centre" };

    async function carrega(opcions) {
      const wrapper = muntaDetall(opcions);
      await vi.waitFor(() => expect(wrapper.find(".library-card").exists()).toBe(true));
      await flushPromises();
      return wrapper;
    }

    it("cada biblioteca té el seu botó i afegeix el llibre amb aquella biblioteca", async () => {
      const wrapper = await carrega({ autenticat: true });

      await wrapper.get(".library-card .add-button").trigger("click");

      expect(useComandaStore().llibres).toEqual([
        { id: 12, titol: "La plaça del Diamant", autor: "Mercè Rodoreda", portada: "", biblioteca: CENTRE },
      ]);
      expect(wrapper.get(".library-card .add-button").text()).toBe("Afegit a la comanda");
      expect(wrapper.get(".library-card .add-button").attributes("disabled")).toBeDefined();
      expect(wrapper.get(".en-comanda").text()).toContain("Aquest llibre ja és a la teva comanda.");
    });

    it("no barreja biblioteques i explica per què", async () => {
      const wrapper = await carrega({ autenticat: true });
      useComandaStore().afegirLlibre({
        id: 30,
        titol: "Solitud",
        autor: "Víctor Català",
        biblioteca: { id: 8, nom: "Biblioteca Montbau" },
      });

      await wrapper.get(".library-card .add-button").trigger("click");

      expect(useComandaStore().teLlibre(12)).toBe(false);
      expect(wrapper.get(".avis-comanda").text()).toBe(
        "La comanda només pot tenir llibres d'una biblioteca. Confirma-la o treu-ne els llibres de " +
          "Biblioteca Montbau abans d'afegir-ne d'una altra.",
      );
    });

    it("sense sessió, el botó porta a iniciar-la", async () => {
      const wrapper = await carrega();

      await wrapper.get(".library-card .add-button").trigger("click");

      expect(push).toHaveBeenCalledWith({ name: "inici-sessio" });
      expect(useComandaStore().nombreLlibres).toBe(0);
    });

    it.each(["biblioteca", "repartidor"])("amb el rol %s no hi ha botó", async (rol) => {
      const wrapper = await carrega({ autenticat: true, rol });

      expect(wrapper.find(".library-card .add-button").exists()).toBe(false);
    });
  });
});
