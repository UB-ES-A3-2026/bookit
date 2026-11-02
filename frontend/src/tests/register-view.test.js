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

function ompleFormulariBiblioteca(element, dades = {
  correu: "biblioteca@example.com",
  nom: "Biblioteca Central",
  dniNie: "12345678Z",
}) {
  element.querySelector("#correu-oficial").value = dades.correu;
  element.querySelector("#correu-oficial").dispatchEvent(
    new Event("input", { bubbles: true }),
  );
  element.querySelector("#nom-biblioteca").value = dades.nom;
  element.querySelector("#nom-biblioteca").dispatchEvent(
    new Event("input", { bubbles: true }),
  );
  element.querySelector("#dni-nie-responsable").value = dades.dniNie;
  element.querySelector("#dni-nie-responsable").dispatchEvent(
    new Event("input", { bubbles: true }),
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

  it("mostra l'avís i no envia el formulari per als tipus no implementats", async () => {
    const element = renderitza();

    element.querySelector("button.account-type__option:nth-of-type(2)").click();
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

  it("valida i envia el registre de biblioteca", async () => {
    axios.post.mockResolvedValue({ status: 201 });
    const element = renderitza();

    element.querySelector("button.account-type__option:nth-of-type(3)").click();
    await nextTick();
    ompleFormulariBiblioteca(element);
    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();
    await nextTick();

    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/api/auth/register/biblioteca/",
      {
        nom: "Biblioteca Central",
        correu: "biblioteca@example.com",
      },
    );
    expect(element.textContent).toContain("Revisa el teu correu");
  });

  it("no envia el registre de biblioteca si falta un camp", async () => {
    const element = renderitza();

    element.querySelector("button.account-type__option:nth-of-type(3)").click();
    await nextTick();
    ompleFormulariBiblioteca(element, { dniNie: "" });
    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();

    expect(element.textContent).toContain(
      "Algún dels camps no és vàlid o no s'ha introduït",
    );
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("mostra l'error de correu duplicat de biblioteca", async () => {
    axios.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          correu: ["Aquest correu correspon a un compte existent"],
        },
      },
    });
    const element = renderitza();

    element.querySelector("button.account-type__option:nth-of-type(3)").click();
    await nextTick();
    ompleFormulariBiblioteca(element);
    element.querySelector("form").dispatchEvent(new Event("submit"));
    await nextTick();
    await nextTick();

    expect(element.textContent).toContain(
      "Aquest correu correspon a un compte existent",
    );
    expect(element.textContent).not.toContain("Revisa el teu correu");
  });
});
