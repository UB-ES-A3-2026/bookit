import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../services/api.js";
import {
  apuntaLlistaEspera,
  llistaBibliotequesAmbEstoc,
} from "../services/biblioteques.js";

vi.mock("../services/api.js", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("servei de biblioteques amb estoc", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("consulta les biblioteques amb estoc d'un llibre", async () => {
    const dades = {
      biblioteques: [],
      ordenada_per_distancia: false,
      missatge: "Cap biblioteca te aquest llibre en estoc",
    };
    api.get.mockResolvedValue({ data: dades });

    await expect(llistaBibliotequesAmbEstoc(12)).resolves.toEqual(dades);
    expect(api.get).toHaveBeenCalledWith("/cataleg/llibres/12/biblioteques/");
  });

  it("apunta a la llista d'espera i retorna el codi d'estat", async () => {
    const dades = { llibre: 12, data_alta: "2026-11-24T12:00:00Z" };
    api.post.mockResolvedValue({ data: dades, status: 201 });

    await expect(apuntaLlistaEspera(12)).resolves.toEqual({
      data: dades,
      status: 201,
    });
    expect(api.post).toHaveBeenCalledWith("/cataleg/llibres/12/llista-espera/");
  });
});
