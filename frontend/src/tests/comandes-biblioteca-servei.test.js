import { beforeEach, describe, expect, it, vi } from "vitest";
import { marcaComandaPreparada } from "../services/comandesBiblioteca.js";

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock("../services/api.js", () => ({ default: api }));

beforeEach(() => {
  vi.resetAllMocks();
});

describe("marcaComandaPreparada", () => {
  it("envia el POST a la ruta de la comanda, sense cos, i retorna la comanda", async () => {
    const comanda = { id: 12, estat: "preparada" };
    api.post.mockResolvedValue({ data: comanda });

    await expect(marcaComandaPreparada(12)).resolves.toEqual(comanda);
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledWith("/prestecs/biblioteca/comandes/12/preparada/");
  });

  it("propaga l'error de l'API", async () => {
    const error = { response: { status: 409, data: { detail: "Aquesta comanda ja està llesta per a recollida." } } };
    api.post.mockRejectedValue(error);

    await expect(marcaComandaPreparada(12)).rejects.toBe(error);
  });
});
