import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";

const MONTBAU = { id: 3, nom: "Biblioteca Montbau" };
const SAGRADA_FAMILIA = { id: 4, nom: "Biblioteca Sagrada Família" };

function llibre(id, biblioteca = MONTBAU) {
  return { id, titol: `Llibre ${id}`, autor: "Autor", portada: "", biblioteca };
}

function entra(id) {
  useSessioStore().iniciarSessio({ accessToken: `token-${id}`, usuari: { id }, rol: "usuari" });
}

describe("comanda", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    entra(25);
  });

  it("afegeix un llibre amb la seva biblioteca i el desa per a l'usuari", () => {
    const comanda = useComandaStore();

    expect(comanda.afegirLlibre(llibre(7))).toBe(true);

    expect(comanda.nombreLlibres).toBe(1);
    expect(comanda.biblioteca).toEqual(MONTBAU);
    expect(JSON.parse(localStorage.getItem("bookit.comanda.25"))).toEqual([llibre(7)]);
  });

  it("no permet afegir dues vegades el mateix llibre", () => {
    const comanda = useComandaStore();

    expect(comanda.afegirLlibre(llibre(7))).toBe(true);
    expect(comanda.afegirLlibre(llibre(7))).toBe(false);
    expect(comanda.nombreLlibres).toBe(1);
  });

  it("no afegeix un llibre sense biblioteca", () => {
    const comanda = useComandaStore();

    expect(comanda.afegirLlibre({ ...llibre(7), biblioteca: null })).toBe(false);
    expect(comanda.nombreLlibres).toBe(0);
  });

  it("no barreja llibres de biblioteques diferents", () => {
    const comanda = useComandaStore();
    comanda.afegirLlibre(llibre(7));

    expect(comanda.esDUnaAltraBiblioteca(SAGRADA_FAMILIA)).toBe(true);
    expect(comanda.esDUnaAltraBiblioteca(MONTBAU)).toBe(false);
    expect(comanda.afegirLlibre(llibre(9, SAGRADA_FAMILIA))).toBe(false);
    expect(comanda.afegirLlibre(llibre(9))).toBe(true);
    expect(comanda.nombreLlibres).toBe(2);
  });

  it("es conserva encara que es torni a obrir l'aplicació", () => {
    useComandaStore().afegirLlibre(llibre(7));

    setActivePinia(createPinia());
    entra(25);

    expect(useComandaStore().llibres).toEqual([llibre(7)]);
  });

  it("cada usuari té la seva comanda", () => {
    const comanda = useComandaStore();
    comanda.afegirLlibre(llibre(7));

    useSessioStore().tancarSessio();
    comanda.sincronitza();
    expect(comanda.llibres).toEqual([]);

    entra(30);
    comanda.sincronitza();
    expect(comanda.llibres).toEqual([]);
    comanda.afegirLlibre(llibre(9));

    entra(25);
    comanda.sincronitza();
    expect(comanda.llibres).toEqual([llibre(7)]);
  });

  it("permet treure un llibre de la comanda", () => {
    const comanda = useComandaStore();
    comanda.afegirLlibre(llibre(7));

    comanda.eliminarLlibre(7);

    expect(comanda.llibres).toEqual([]);
    expect(comanda.biblioteca).toBeNull();
    expect(localStorage.getItem("bookit.comanda.25")).toBe("[]");
  });

  it("detecta quan se supera el límit de cinc llibres", () => {
    const comanda = useComandaStore();

    for (let id = 1; id <= 6; id += 1) {
      comanda.afegirLlibre(llibre(id));
    }

    expect(comanda.nombreLlibres).toBe(6);
    expect(comanda.superaLimit).toBe(true);
  });

  it("buidar elimina tots els llibres i la comanda desada", () => {
    const comanda = useComandaStore();
    comanda.afegirLlibre(llibre(7));

    comanda.buidar();

    expect(comanda.llibres).toEqual([]);
    expect(comanda.superaLimit).toBe(false);
    expect(localStorage.getItem("bookit.comanda.25")).toBeNull();
  });

  it("ignora una comanda desada que no es pot llegir", () => {
    localStorage.setItem("bookit.comanda.25", "no és JSON");
    setActivePinia(createPinia());

    expect(useComandaStore().llibres).toEqual([]);
    expect(localStorage.getItem("bookit.comanda.25")).toBeNull();
  });
});
