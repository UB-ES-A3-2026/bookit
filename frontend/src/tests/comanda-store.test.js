import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useComandaStore } from "../stores/comanda.js";

describe("comanda", () => {
  beforeEach(() => {
    sessionStorage.clear();
    setActivePinia(createPinia());
  });

  it("afegeix un llibre i el conserva a la sessió", () => {
    const comanda = useComandaStore();
    const llibre = {
      id: 7,
      titol: "La plaça del Diamant",
      autor: "Mercè Rodoreda",
      portada: "",
    };

    expect(comanda.afegirLlibre(llibre)).toBe(true);
    expect(comanda.nombreLlibres).toBe(1);
    expect(JSON.parse(sessionStorage.getItem("bookit.comanda"))).toEqual([
      { ...llibre, biblioteca: null },
    ]);
  });

  it("no permet afegir dues vegades el mateix llibre", () => {
    const comanda = useComandaStore();
    const llibre = { id: 7, titol: "Solitud", autor: "Víctor Català" };

    expect(comanda.afegirLlibre(llibre)).toBe(true);
    expect(comanda.afegirLlibre(llibre)).toBe(false);
    expect(comanda.nombreLlibres).toBe(1);
  });

  it("permet treure un llibre de la comanda", () => {
    const comanda = useComandaStore();
    comanda.afegirLlibre({ id: 7, titol: "Solitud", autor: "Víctor Català" });

    comanda.eliminarLlibre(7);

    expect(comanda.llibres).toEqual([]);
    expect(sessionStorage.getItem("bookit.comanda")).toBe("[]");
  });
});
