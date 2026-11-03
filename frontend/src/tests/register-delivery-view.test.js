import axios from "axios";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RegisterView from "../views/RegisterView.vue";

const push = vi.fn();

vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

function muntaRegistre() {
  return mount(RegisterView, {
    global: {
      components: {
        RouterLink: {
          template: "<a><slot /></a>",
        },
      },
    },
  });
}

async function obreFormulariRepartidor() {
  const wrapper = muntaRegistre();
  const boto = wrapper
    .findAll("button")
    .find((element) => element.text().includes("Repartidor"));
  await boto.trigger("click");
  return wrapper;
}

async function ompleFormulari(wrapper, canvis = {}) {
  const dades = {
    "repartidor-correu": "repartidor@example.cat",
    "repartidor-nom": "Laia",
    "repartidor-cognoms": "Martí Roca",
    "repartidor-dni": "X1234567L",
    "repartidor-telefon": "612345678",
    "repartidor-seguretat-social": "081234567890",
    "repartidor-contrasenya": "Llibres-de-tardor-24",
    "repartidor-confirmar-contrasenya": "Llibres-de-tardor-24",
    ...canvis,
  };

  await wrapper.get("#repartidor-vehicle").setValue("bici");

  for (const [id, valor] of Object.entries(dades)) {
    await wrapper.get(`#${id}`).setValue(valor);
  }
}

describe("formulari de registre de repartidor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("mostra o amaga la matrícula segons el vehicle", async () => {
    const wrapper = await obreFormulariRepartidor();
    const vehicle = wrapper.get("#repartidor-vehicle");

    expect(wrapper.find("#repartidor-matricula").exists()).toBe(false);

    await vehicle.setValue("moto");
    expect(wrapper.find("#repartidor-matricula").exists()).toBe(true);

    await vehicle.setValue("bici");
    expect(wrapper.find("#repartidor-matricula").exists()).toBe(false);
  });

  it("mostra els errors dels camps obligatoris i de format", async () => {
    const wrapper = await obreFormulariRepartidor();
    await wrapper.get("form").trigger("submit");

    expect(wrapper.get("#repartidor-correu-error").text()).toBe(
      "Aquest camp és obligatori.",
    );
    expect(wrapper.get("#repartidor-dni-error").text()).toBe(
      "Aquest camp és obligatori.",
    );

    await wrapper.get("#repartidor-correu").setValue("correu");
    await wrapper.get("#repartidor-dni").setValue("12345678A");
    await wrapper.get("#repartidor-telefon").setValue("612");
    await wrapper.get("#repartidor-vehicle").setValue("bici");
    await wrapper.get("#repartidor-nom").setValue("Laia");
    await wrapper.get("#repartidor-cognoms").setValue("Roca");
    await wrapper
      .get("#repartidor-seguretat-social")
      .setValue("081234567890");
    await wrapper.get("#repartidor-contrasenya").setValue("secret");
    await wrapper
      .get("#repartidor-confirmar-contrasenya")
      .setValue("diferent");
    await wrapper.get("form").trigger("submit");

    expect(wrapper.get("#repartidor-correu-error").text()).toContain(
      "adreça vàlida",
    );
    expect(wrapper.get("#repartidor-dni-error").text()).toContain("no és vàlid");
    expect(wrapper.get("#repartidor-telefon-error").text()).toContain(
      "9 xifres",
    );
    expect(
      wrapper.get("#repartidor-confirmar-contrasenya-error").text(),
    ).toBe("Les contrasenyes no coincideixen.");
    expect(axios.post).not.toHaveBeenCalled();
  });

  it("no envia matrícula quan el vehicle és bicicleta", async () => {
    const wrapper = await obreFormulariRepartidor();
    await ompleFormulari(wrapper);
    axios.post.mockResolvedValue({ status: 201 });

    await wrapper.get("form").trigger("submit");

    expect(axios.post).toHaveBeenCalledWith(
      "http://localhost:8000/api/auth/register/repartidor/",
      {
        nom: "Laia",
        cognoms: "Martí Roca",
        correu: "repartidor@example.cat",
        dni: "X1234567L",
        telefon: "612345678",
        vehicle: "bici",
        num_seguretat_social: "081234567890",
        contrasenya: "Llibres-de-tardor-24",
      },
    );
  });

  it("envia la matrícula per a moto", async () => {
    const wrapper = await obreFormulariRepartidor();
    await ompleFormulari(wrapper);
    await wrapper.get("#repartidor-vehicle").setValue("moto");
    await wrapper.get("#repartidor-matricula").setValue("1234 BCD");
    axios.post.mockResolvedValue({ status: 201 });

    await wrapper.get("form").trigger("submit");

    expect(axios.post.mock.calls[0][1]).toMatchObject({
      vehicle: "moto",
      matricula: "1234 BCD",
    });
  });

  it("mostra els errors de validació retornats pel backend", async () => {
    const wrapper = await obreFormulariRepartidor();
    await ompleFormulari(wrapper);
    axios.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          correu: ["Aquest correu ja està registrat."],
          dni: ["Aquest DNI ja està registrat."],
        },
      },
    });

    await wrapper.get("form").trigger("submit");

    expect(wrapper.get("#repartidor-correu-error").text()).toBe(
      "Aquest correu ja està registrat.",
    );
    expect(wrapper.get("#repartidor-dni-error").text()).toBe(
      "Aquest DNI ja està registrat.",
    );
  });
});
