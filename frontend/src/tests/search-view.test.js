import axios from "axios";
import { h } from "vue";
import { mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SearchView from "../views/SearchView.vue";

const push = vi.fn();
const route = { query: {} };

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
  },
}));

// Les notificacions tenen els seus tests: aquí no fa falta el client de l'API.
vi.mock("../services/notificacions.js", () => ({}));

vi.mock("vue-router", () => ({
  useRoute: () => route,
  useRouter: () => ({ push }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

const RouterLinkStub = {
  props: ["to"],
  setup(props, { slots }) {
    return () =>
      h(
        "a",
        { "data-destinacio": JSON.stringify(props.to) },
        slots.default?.(),
      );
  },
};

function muntaCerca(query = {}) {
  route.query = query;
  return mount(SearchView, {
    global: {
      plugins: [createPinia()],
      components: { RouterLink: RouterLinkStub },
    },
  });
}

describe("pàgina de resultats de la cerca", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    axios.get.mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
      },
    });
  });

  it("consulta l'API amb el text cercat i la pàgina", async () => {
    const wrapper = muntaCerca({ q: "Rodoreda", pagina: "2" });
    await vi.waitFor(() => expect(axios.get).toHaveBeenCalled());

    expect(axios.get).toHaveBeenCalledWith(
      "http://localhost:8000/api/cataleg/llibres/",
      { params: { q: "Rodoreda", page: 2 } },
    );
    expect(wrapper.get("h1").text()).toBe("Resultats de la cerca");
    expect(wrapper.text()).toContain("Has cercat «Rodoreda».");
  });

  it("mostra els llibres i les seves dades", async () => {
    axios.get.mockResolvedValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            titol: "La plaça del Diamant",
            autor: "Mercè Rodoreda",
            disponible: true,
            portada: "",
            mitjana_valoracions: 4.25,
            nombre_valoracions: 12,
          },
        ],
      },
    });
    const wrapper = muntaCerca({ q: "Rodoreda" });
    await vi.waitFor(() => expect(wrapper.find(".llibre").exists()).toBe(true));

    expect(wrapper.text()).toContain("La plaça del Diamant");
    expect(wrapper.text()).toContain("Mercè Rodoreda");
    expect(wrapper.text()).toContain("Disponible");
    expect(wrapper.text()).toContain("4,3 de 5 · 12 valoracions");
    expect(wrapper.get(".add-button").text()).toBe("Afegir a la comanda");
  });

  it("no permet afegir un llibre sense estoc i mostra el missatge exacte", async () => {
    axios.get.mockResolvedValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 9,
            titol: "Solitud",
            autor: "Víctor Català",
            disponible: false,
            portada: "",
            mitjana_valoracions: null,
            nombre_valoracions: 0,
          },
        ],
      },
    });
    const wrapper = muntaCerca({ q: "Solitud" });
    await vi.waitFor(() => expect(wrapper.find(".llibre").exists()).toBe(true));

    expect(wrapper.find(".stock-warning").text()).toContain(
      "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera",
    );
    expect(wrapper.get(".add-button").attributes("disabled")).toBeDefined();
    const waitButton = wrapper.get(".wait-button");
    await waitButton.trigger("click");
    expect(waitButton.text()).toBe("Apuntat a la llista d'espera");
  });

  it("enllaça cada resultat amb el detall i hi passa les dades del llibre", async () => {
    axios.get.mockResolvedValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 12,
            titol: "La plaça del Diamant",
            autor: "Mercè Rodoreda",
            disponible: true,
            portada: "https://exemple.cat/portada.jpg",
            mitjana_valoracions: 4.25,
            nombre_valoracions: 12,
          },
        ],
      },
    });
    const wrapper = muntaCerca({ q: "Rodoreda", pagina: "2" });
    await vi.waitFor(() => expect(wrapper.find(".detall-link").exists()).toBe(true));

    expect(wrapper.get(".detall-link").text()).toBe("Veure biblioteques");
    expect(JSON.parse(wrapper.get(".detall-link").attributes("data-destinacio"))).toEqual({
      name: "detall-llibre",
      params: { id: 12 },
      query: {
        titol: "La plaça del Diamant",
        autor: "Mercè Rodoreda",
        portada: "https://exemple.cat/portada.jpg",
        cerca: "Rodoreda",
        pagina: 2,
      },
    });
  });

  it("mostra el missatge quan no hi ha resultats", async () => {
    const wrapper = muntaCerca({ q: "llibre inexistent" });
    await vi.waitFor(() =>
      expect(wrapper.find(".sense-resultats").exists()).toBe(true),
    );

    expect(wrapper.find(".sense-resultats").text()).toBe(
      "No s'ha trobat el llibre cercat, assegura't que l'informació introduïda sigui correcta",
    );
    expect(wrapper.find(".llista-resultats").exists()).toBe(false);
  });

  it("mostra l'error de l'API i permet tornar-ho a provar", async () => {
    axios.get.mockRejectedValue(new Error("servidor aturat"));
    const wrapper = muntaCerca({ q: "Rodoreda" });
    await vi.waitFor(() => expect(wrapper.find(".estat-error").exists()).toBe(true));

    expect(wrapper.text()).toContain("No s'ha pogut fer la cerca.");
    expect(wrapper.get("button").text()).toBe("Tornar-ho a provar");
  });

  it("no consulta l'API sense text cercat", async () => {
    const wrapper = muntaCerca();
    await vi.waitFor(() => expect(wrapper.find(".description").exists()).toBe(true));

    expect(axios.get).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain(
      "Escriu el títol, l'autor o l'ISBN al cercador de la pàgina d'inici.",
    );
  });
});
