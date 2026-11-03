import { createApp, nextTick } from "vue";
import { afterEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

const route = vi.hoisted(() => ({
  params: {
    uidb64: "uid/1",
    token: "token+1",
  },
}));

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock("vue-router", () => ({
  useRoute: () => route,
}));

let app;

function renderitza() {
  const element = document.createElement("div");
  document.body.appendChild(element);
  app = createApp(VerifyLibraryView);
  app.mount(element);
  return element;
}

async function esperaResposta() {
  await Promise.resolve();
  await nextTick();
  await nextTick();
}

afterEach(() => {
  app?.unmount();
  document.body.innerHTML = "";
  route.params = { uidb64: "uid/1", token: "token+1" };
  vi.clearAllMocks();
});

describe("verificació del compte de biblioteca", () => {
  it("mostra la confirmació quan l'API valida el compte", async () => {
    axios.get.mockResolvedValue({
      data: { detail: "El compte s'ha verificat correctament." },
    });
    const element = renderitza();

    await esperaResposta();

    expect(axios.get).toHaveBeenCalledWith(
      "http://localhost:8000/api/auth/verify/biblioteca/uid%2F1/token%2B1/",
    );
    expect(element.textContent).toContain(
      "El compte s'ha verificat correctament.",
    );
    expect(element.textContent).toContain("Ja pots iniciar sessió");
  });

  it("mostra l'error retornat per un enllaç invàlid", async () => {
    axios.get.mockRejectedValue({
      response: {
        data: { detail: "L'enllaç no és vàlid." },
      },
    });
    const element = renderitza();

    await esperaResposta();

    expect(element.textContent).toContain("L'enllaç no és vàlid.");
    expect(element.querySelector('[role="alert"]')).not.toBeNull();
  });

  it("no crida l'API si falta el token", async () => {
    route.params = { uidb64: "uid/1", token: "" };
    const element = renderitza();

    await esperaResposta();

    expect(axios.get).not.toHaveBeenCalled();
    expect(element.textContent).toContain(
      "L'enllaç de verificació no és vàlid o ha caducat.",
    );
  });
});
