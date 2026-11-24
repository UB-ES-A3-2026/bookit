import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../services/api.js";
import {
  afegeixAdreca,
  editaAdreca,
  llistaAdreces,
  suprimeixAdreca,
} from "../services/adreces.js";

vi.mock("../services/api.js", () => ({
  default: {
    delete: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("servei d'adreces", () => {
  it("llista les adreces pròpies", async () => {
    const resposta = [{ id: 1 }];
    api.get.mockResolvedValue({ data: resposta });

    await expect(llistaAdreces()).resolves.toBe(resposta);
    expect(api.get).toHaveBeenCalledWith("/usuaris/adreces/");
  });

  it("afegeix una adreça", async () => {
    const dades = { municipi: "Barcelona" };
    const resposta = { data: { id: 1, ...dades } };
    api.post.mockResolvedValue(resposta);

    await expect(afegeixAdreca(dades)).resolves.toBe(resposta.data);
    expect(api.post).toHaveBeenCalledWith("/usuaris/adreces/", dades);
  });

  it("actualitza una adreça amb PATCH", async () => {
    const dades = { carrer: "Carrer Nou 5" };
    const resposta = { data: { id: 3, ...dades } };
    api.patch.mockResolvedValue(resposta);

    await expect(editaAdreca(3, dades)).resolves.toBe(resposta.data);
    expect(api.patch).toHaveBeenCalledWith("/usuaris/adreces/3/", dades);
  });

  it("suprimeix una adreça", async () => {
    await suprimeixAdreca(4);

    expect(api.delete).toHaveBeenCalledWith("/usuaris/adreces/4/");
  });
});
