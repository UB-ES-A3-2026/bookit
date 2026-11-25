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

beforeEach(() => {
  vi.resetAllMocks();
  pinia = createPinia();
  setActivePinia(pinia);
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

async function obre(ruta, rol) {
  if (rol) {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol });
  }
  await router.push(ruta);
  wrapper = mount(App, { global: { plugins: [pinia, router] } });
  await flushPromises();
}

describe("ruta del dia amb el router i el servei", () => {
  it("des de l'espai del repartidor obre la ruta i demana l'endpoint del contracte", async () => {
    api.get.mockResolvedValue({
      data: [
        {
          id: 19,
          ordre: 2,
          tipus: "lliurament",
          comanda: 12,
          estat: "preparada",
          llibres: [],
          adreca: { biblioteca: null, text: "C/ Major 1", latitud: null, longitud: null },
        },
        {
          id: 18,
          ordre: 1,
          tipus: "recollida",
          comanda: 12,
          estat: "preparada",
          llibres: [],
          adreca: {
            biblioteca: { id: 3, nom: "Biblioteca Central" },
            text: null,
            latitud: null,
            longitud: null,
          },
        },
      ],
    });
    await obre("/repartidor", "repartidor");

    await wrapper.get('a[href="/repartidor/ruta"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("ruta-repartidor");
    expect(api.get).toHaveBeenCalledWith("/prestecs/repartidor/ruta-avui/");
    expect(wrapper.findAll(".lloc").map((element) => element.text())).toEqual([
      "Biblioteca Central",
      "C/ Major 1",
    ]);
  });

  it("sense sessió no demana la ruta i porta a iniciar sessió", async () => {
    await obre("/repartidor/ruta");

    expect(router.currentRoute.value.name).toBe("inici-sessio");
    expect(api.get).not.toHaveBeenCalledWith("/prestecs/repartidor/ruta-avui/");
  });

  it("un usuari torna a l'inici sense demanar la ruta", async () => {
    api.get.mockResolvedValue({ data: [] });
    await obre("/repartidor/ruta", "usuari");

    expect(router.currentRoute.value.name).toBe("home");
    expect(api.get).not.toHaveBeenCalledWith("/prestecs/repartidor/ruta-avui/");
  });
});

describe("accions de les parades amb el servei de veritat (US13-T5)", () => {
  const paradaPendent = {
    id: 18,
    ordre: 1,
    tipus: "recollida",
    comanda: 12,
    estat: "preparada",
    estat_parada: "pendent",
    motiu: "",
    llibres: [],
    adreca: { biblioteca: { id: 3, nom: "Biblioteca Central" }, text: null, latitud: null, longitud: null },
  };

  it("completar una parada fa POST a l'endpoint de completar", async () => {
    api.get.mockResolvedValue({ data: [paradaPendent] });
    api.post.mockResolvedValue({ data: { id: 18, estat: "completada" } });
    await obre("/repartidor/ruta", "repartidor");

    await wrapper.find(".boto-completada").trigger("click");
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith("/prestecs/repartidor/parades/18/completar/");
  });

  it("marcar-la fallida fa POST a l'endpoint de fallida amb el motiu", async () => {
    api.get.mockResolvedValue({ data: [paradaPendent] });
    api.post.mockResolvedValue({ data: { id: 18, estat: "fallida" } });
    await obre("/repartidor/ruta", "repartidor");

    await wrapper.find(".boto-fallida").trigger("click");
    await wrapper.find("textarea").setValue("Biblioteca tancada");
    await wrapper.find(".form-fallida").trigger("submit");
    await flushPromises();

    expect(api.post).toHaveBeenCalledWith("/prestecs/repartidor/parades/18/fallida/", {
      motiu: "Biblioteca tancada",
    });
  });
});
