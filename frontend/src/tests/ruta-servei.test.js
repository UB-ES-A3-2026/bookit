import { beforeEach, describe, expect, it, vi } from "vitest";
import { completaParada, fallaParada } from "../services/ruta.js";

// US13-T6: el servei de les parades crida els endpoints del contracte.
const api = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}));

vi.mock("../services/api.js", () => ({ default: api }));

beforeEach(() => {
  vi.resetAllMocks();
});

describe("completaParada", () => {
  it("fa POST a l'endpoint de completar i retorna la parada", async () => {
    const parada = { id: 18, estat: "completada", completada_el: "2026-11-24T10:00:00Z" };
    api.post.mockResolvedValue({ data: parada });

    await expect(completaParada(18)).resolves.toEqual(parada);
    expect(api.post).toHaveBeenCalledWith("/prestecs/repartidor/parades/18/completar/");
  });

  it("propaga l'error de l'API", async () => {
    const error = Object.assign(new Error("conflicte"), { response: { status: 409 } });
    api.post.mockRejectedValue(error);

    await expect(completaParada(18)).rejects.toBe(error);
  });
});

describe("fallaParada", () => {
  it("fa POST a l'endpoint de fallida amb el motiu i retorna la parada", async () => {
    const parada = { id: 19, estat: "fallida", motiu: "Biblioteca tancada" };
    api.post.mockResolvedValue({ data: parada });

    await expect(fallaParada(19, "Biblioteca tancada")).resolves.toEqual(parada);
    expect(api.post).toHaveBeenCalledWith("/prestecs/repartidor/parades/19/fallida/", {
      motiu: "Biblioteca tancada",
    });
  });

  it("propaga l'error de validació del motiu", async () => {
    const error = Object.assign(new Error("dades invàlides"), {
      response: { status: 400, data: { motiu: ["Aquest camp és obligatori."] } },
    });
    api.post.mockRejectedValue(error);

    await expect(fallaParada(19, "")).rejects.toBe(error);
  });
});
