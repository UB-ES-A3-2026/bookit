import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PrestecsView from "../views/PrestecsView.vue";

const serveiPrestecs = vi.hoisted(() => ({
  llistaPrestecs: vi.fn(),
}));

vi.mock("../services/prestecs.js", () => serveiPrestecs);

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

function muntaPrestecs() {
  return mount(PrestecsView, {
    global: {
      plugins: [createPinia()],
      components: {
        RouterLink: {
          template: "<a><slot /></a>",
        },
      },
    },
  });
}

describe("Els meus préstecs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("mostra les dades del préstec i la data límit", async () => {
    serveiPrestecs.llistaPrestecs.mockResolvedValue([
      {
        id: 21,
        llibre: {
          id: 7,
          titol: "La plaça del Diamant",
          autor: "Mercè Rodoreda",
          portada: "",
        },
        biblioteca: { id: 3, nom: "Biblioteca Montbau" },
        data_inici: "2026-10-10",
        data_limit: "2026-11-09",
        termini_superat: true,
      },
    ]);

    const wrapper = muntaPrestecs();
    await vi.waitFor(() => expect(wrapper.find(".prestec").exists()).toBe(true));

    expect(wrapper.text()).toContain("La plaça del Diamant");
    expect(wrapper.text()).toContain("Mercè Rodoreda");
    expect(wrapper.text()).toContain("Biblioteca Montbau");
    expect(wrapper.text()).toContain("09/11/2026");
    expect(wrapper.get(".avis-superat").text()).toBe(
      "Termini de devolució superat",
    );
  });

  it("no mostra l'avís quan el termini no està superat", async () => {
    serveiPrestecs.llistaPrestecs.mockResolvedValue([
      {
        id: 22,
        llibre: {
          id: 9,
          titol: "Solitud",
          autor: "Víctor Català",
          portada: "",
        },
        biblioteca: { id: 3, nom: "Biblioteca Montbau" },
        data_inici: "2026-11-18",
        data_limit: "2026-12-18",
        termini_superat: false,
      },
    ]);

    const wrapper = muntaPrestecs();
    await vi.waitFor(() => expect(wrapper.find(".prestec").exists()).toBe(true));

    expect(wrapper.find(".avis-superat").exists()).toBe(false);
  });

  it("mostra el missatge quan no hi ha préstecs", async () => {
    serveiPrestecs.llistaPrestecs.mockResolvedValue([]);

    const wrapper = muntaPrestecs();
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain("No tens cap llibre en préstec"),
    );

    expect(wrapper.text()).toContain("No tens cap llibre en préstec");
  });

  it("mostra l'error i permet tornar-ho a provar", async () => {
    serveiPrestecs.llistaPrestecs.mockRejectedValueOnce(new Error("API aturada"));

    const wrapper = muntaPrestecs();
    await vi.waitFor(() => expect(wrapper.find(".estat-error").exists()).toBe(true));

    expect(wrapper.text()).toContain(
      "No s'han pogut carregar els llibres en préstec.",
    );

    serveiPrestecs.llistaPrestecs.mockResolvedValueOnce([]);
    await wrapper.get(".secondary-button").trigger("click");
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain("No tens cap llibre en préstec"),
    );
  });
});
