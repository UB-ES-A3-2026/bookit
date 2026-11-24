import { createApp, nextTick } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const URL_API = "http://localhost:8000/api/auth/verify/biblioteca/uid%2F1/token%2B1/";

let app;

// Deixa que s'acabin les peticions simulades i el renderitzat que les segueix.
const esperaRenderitzat = () => new Promise((resolve) => setTimeout(resolve));

async function renderitza(ruta = "/verificacio/biblioteca/uid%2F1/token%2B1") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<p>Inici</p>" } },
      { path: "/inicia-sessio", name: "inici-sessio", component: { template: "<p>Login</p>" } },
      {
        path: "/verificacio/biblioteca/:uidb64?/:token?",
        name: "verificacio-biblioteca",
        component: VerifyLibraryView,
      },
    ],
  });
  router.push(ruta);
  await router.isReady();

  const element = document.createElement("div");
  document.body.appendChild(element);
  app = createApp(VerifyLibraryView);
  app.use(router);
  app.mount(element);
  await esperaRenderitzat();
  return element;
}

function escriu(element, id, valor) {
  const input = element.querySelector(`#${id}`);
  input.value = valor;
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

async function envia(element, contrasenya, confirmacio = contrasenya) {
  escriu(element, "contrasenya", contrasenya);
  escriu(element, "confirmar-contrasenya", confirmacio);
  element.querySelector("form").dispatchEvent(new Event("submit"));
  await esperaRenderitzat();
}

const errorDe = (element, id) => element.querySelector(`#${id}-error`).textContent.trim();

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  vi.clearAllMocks();
});

describe("verificació del compte de biblioteca", () => {
  it("comprova l'enllaç i demana la contrasenya sense activar res", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    const element = await renderitza();

    expect(axios.get).toHaveBeenCalledWith(URL_API);
    expect(axios.post).not.toHaveBeenCalled();
    expect(element.textContent).toContain("biblioteca@example.com");
    expect(element.querySelector("#contrasenya")).not.toBeNull();
    expect(element.querySelector("#confirmar-contrasenya")).not.toBeNull();
  });

  it("envia la contrasenya i mostra la confirmació amb l'enllaç per iniciar sessió", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    axios.post.mockResolvedValue({
      data: { detail: "El compte de biblioteca s'ha verificat correctament." },
    });
    const element = await renderitza();

    await envia(element, "Llibres-de-tardor-24");

    expect(axios.post).toHaveBeenCalledWith(URL_API, {
      contrasenya: "Llibres-de-tardor-24",
    });
    expect(element.textContent).toContain(
      "El compte de biblioteca s'ha verificat correctament.",
    );
    expect(element.querySelector('a[href="/inicia-sessio"]')).not.toBeNull();
  });

  it("no envia res si falta la contrasenya", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    const element = await renderitza();

    await envia(element, "", "");

    expect(errorDe(element, "contrasenya")).toBe("Aquest camp és obligatori.");
    expect(errorDe(element, "confirmar-contrasenya")).toBe("Aquest camp és obligatori.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("no envia res si les contrasenyes no coincideixen", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    const element = await renderitza();

    await envia(element, "Llibres-de-tardor-24", "Una-altra-cosa-24");

    expect(errorDe(element, "confirmar-contrasenya")).toBe("Les contrasenyes no coincideixen.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("mostra els motius si el backend rebutja la contrasenya i deixa tornar-ho a provar", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    axios.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          contrasenya: ["Aquesta contrasenya és massa curta. Ha de tenir com a mínim 8 caràcters."],
        },
      },
    });
    const element = await renderitza();

    await envia(element, "curta1");

    expect(errorDe(element, "contrasenya")).toContain("massa curta");
    expect(element.querySelector("form")).not.toBeNull();
  });

  it("en tornar a escriure se n'esborra l'error", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    const element = await renderitza();
    await envia(element, "", "");

    escriu(element, "contrasenya", "Llibres-de-tardor-24");
    await nextTick();

    expect(errorDe(element, "contrasenya")).toBe("");
  });

  it("mostra l'error si l'enllaç no és vàlid", async () => {
    axios.get.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: "L'enllaç de verificació no és vàlid o ha caducat." },
      },
    });
    const element = await renderitza();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "L'enllaç de verificació no és vàlid o ha caducat.",
    );
    expect(element.querySelector("form")).toBeNull();
  });

  it("mostra l'error si l'enllaç caduca mentre s'omple el formulari", async () => {
    axios.get.mockResolvedValue({ data: { correu: "biblioteca@example.com" } });
    axios.post.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: "L'enllaç de verificació no és vàlid o ha caducat." },
      },
    });
    const element = await renderitza();

    await envia(element, "Llibres-de-tardor-24");

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "L'enllaç de verificació no és vàlid o ha caducat.",
    );
  });

  it("demana tornar-ho a provar si el servidor no respon", async () => {
    axios.get.mockRejectedValue(new Error("Network Error"));
    const element = await renderitza();

    expect(element.querySelector('[role="alert"]').textContent).toContain(
      "No s'ha pogut verificar el compte. Torna-ho a provar més tard.",
    );
  });

  it("no crida l'API si falta el token", async () => {
    const element = await renderitza("/verificacio/biblioteca/uid%2F1");

    expect(axios.get).not.toHaveBeenCalled();
    expect(element.textContent).toContain(
      "L'enllaç de verificació no és vàlid o ha caducat.",
    );
  });
});
