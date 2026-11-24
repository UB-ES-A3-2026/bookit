import { mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import HomeView from "../views/HomeView.vue";

const push = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

function muntaInici() {
  return mount(HomeView, {
    global: {
      // La capçalera consulta la sessió (Pinia) per saber quins botons mostra.
      plugins: [createPinia()],
      components: {
        RouterLink: {
          template: "<a><slot /></a>",
        },
      },
    },
  });
}

describe("cercador de la pàgina d'inici", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("navega als resultats amb el text retallat", async () => {
    const wrapper = muntaInici();

    await wrapper.get("#cerca-llibres").setValue("  La plaça del Diamant  ");
    await wrapper.get('form[role="search"]').trigger("submit");

    expect(push).toHaveBeenCalledWith({
      name: "cerca",
      query: { q: "La plaça del Diamant" },
    });
  });

  it("no navega amb una cerca buida i retorna el focus al camp", async () => {
    const wrapper = muntaInici();
    const camp = wrapper.get("#cerca-llibres");
    const focus = vi.spyOn(camp.element, "focus");

    await wrapper.get('form[role="search"]').trigger("submit");

    expect(push).not.toHaveBeenCalled();
    expect(focus).toHaveBeenCalled();
  });
});
