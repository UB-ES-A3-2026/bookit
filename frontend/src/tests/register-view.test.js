import { createApp, nextTick } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import RegisterView from "../views/RegisterView.vue";

vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock("vue-router", () => ({
  useRoute: () => ({
    query: {},
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const dadesValides = {
  correu: "anna@example.com",
  nom: "Anna Puig",
  adreca: "C/ Major 1, Barcelona",
  numCarnet: "1234567890",
  contrasenya: "Llibres-de-tardor-24",
  confirmarContrasenya: "Llibres-de-tardor-24",
};

let app;

function renderitza() {
  const element = document.createElement("div");
  document.body.appendChild(element);
  app = createApp(RegisterView);
  app.mount(element);
  return element;
}

function escriu(element, valor) {
  element.value = valor;
  element.dispatchEvent(new Event("input", { bubbles: true }));
}

function ompleFormulari(element, dades = dadesValides) {
  escriu(element.querySelector("#correu"), dades.correu);
  escriu(element.querySelector("#nom"), dades.nom);
  escriu(element.querySelector("#adreca"), dades.adreca);
  escriu(element.querySelector("#num-carnet"), dades.numCarnet);
  escriu(element.querySelector("#contrasenya"), dades.contrasenya);
  escriu(
    element.querySelector("#confirmar-contrasenya"),
    dades.confirmarContrasenya,
  );
}

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  vi.clearAllMocks();
});

describe("formulari de registre", () => {
  it("mostra els errors dels camps obligatoris i no envia el formulari", async () => {
    const element = renderitza();

    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();

    expect(element.querySelectorAll(".register-form__error").length).toBeGreaterThan(0);
    expect(element.textContent).toContain("Aquest camp és obligatori.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("valida el format del correu i la confirmació de contrasenya", async () => {
    const element = renderitza();
    ompleFormulari(element, {
      ...dadesValides,
      correu: "correu-invalid",
      confirmarContrasenya: "diferent",
    });

    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();

    expect(element.textContent).toContain(
      "El correu ha de ser una adreça vàlida",
    );
    expect(element.textContent).toContain("Les contrasenyes no coincideixen.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("mostra l'avís i no envia el formulari si es tria Biblioteca", async () => {
    const element = renderitza();

    // Repartidor ja té formulari (US1.1); Biblioteca encara mostra l'avís.
    element.querySelector("button.account-type__option:nth-of-type(3)").click();
    await nextTick();
    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();

    expect(element.textContent).toContain("Funcionalitat no implementada.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("mostra els errors retornats pel backend", async () => {
    axios.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          correu: ["Aquest correu ja està registrat."],
        },
      },
    });
    const element = renderitza();
    ompleFormulari(element);

    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();
    await nextTick();

    expect(element.textContent).toContain("Aquest correu ja està registrat.");
    expect(axios.post).toHaveBeenCalledOnce();
  });
});
