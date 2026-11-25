import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginView from "../views/LoginView.vue";
import { useSessioStore } from "../stores/sessio.js";
import api from "../services/api.js";

const push = vi.fn();

vi.mock("../services/api.js", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

function muntaLogin() {
  return mount(LoginView, {
    global: {
      components: {
        RouterLink: {
          template: "<a><slot /></a>",
        },
      },
    },
  });
}

describe("caixa d'inici de sessió", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("manté el botó desactivat fins que els dos camps són plens", async () => {
    const wrapper = muntaLogin();
    const boto = wrapper.get('button[type="submit"]');

    expect(boto.element.disabled).toBe(true);

    await wrapper.get("#login-correu").setValue("usuari@example.cat");
    expect(boto.element.disabled).toBe(true);

    await wrapper.get("#login-contrasenya").setValue("secret");
    expect(boto.element.disabled).toBe(false);
  });

  it("permet mostrar i ocultar la contrasenya", async () => {
    const wrapper = muntaLogin();
    const camp = wrapper.get("#login-contrasenya");
    const boto = wrapper.get(".login-form__toggle");

    expect(camp.attributes("type")).toBe("password");
    await boto.trigger("click");
    expect(camp.attributes("type")).toBe("text");
    await boto.trigger("click");
    expect(camp.attributes("type")).toBe("password");
  });

  it("inicia sessió, carrega el perfil i redirigeix segons el rol", async () => {
    api.post.mockResolvedValue({
      data: { access: "access-token", refresh: "refresh-token" },
    });
    api.get.mockResolvedValue({
      data: { id: 1, nom: "Anna", correu: "anna@example.cat", rol: "biblioteca" },
    });
    const wrapper = muntaLogin();

    await wrapper.get("#login-correu").setValue("anna@example.cat");
    await wrapper.get("#login-contrasenya").setValue("secret");
    await wrapper.get("form").trigger("submit");

    expect(api.post).toHaveBeenCalledWith("/auth/login/", {
      correu: "anna@example.cat",
      contrasenya: "secret",
    });
    expect(api.get).toHaveBeenCalledWith("/auth/me/");
    expect(push).toHaveBeenCalledWith({ name: "cataleg" });
    expect(useSessioStore().usuari.nom).toBe("Anna");
    expect(useSessioStore().rol).toBe("biblioteca");
  });

  it("mostra els errors de validació retornats per l'API", async () => {
    api.post.mockRejectedValue({
      response: {
        data: {
          correu: ["El correu no és vàlid."],
          contrasenya: ["La contrasenya és incorrecta."],
        },
      },
    });
    const wrapper = muntaLogin();

    await wrapper.get("#login-correu").setValue("usuari@example.cat");
    await wrapper.get("#login-contrasenya").setValue("secret");
    await wrapper.get("form").trigger("submit");

    expect(wrapper.get("#login-correu-error").text()).toContain(
      "El correu no és vàlid.",
    );
    expect(wrapper.get("#login-contrasenya-error").text()).toContain(
      "La contrasenya és incorrecta.",
    );
    expect(push).not.toHaveBeenCalled();
  });
});
