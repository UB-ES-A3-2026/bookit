import { defineStore } from "pinia";

const COMANDA_STORAGE_KEY = "bookit.comanda";

function llegirComanda() {
  try {
    const dades = JSON.parse(sessionStorage.getItem(COMANDA_STORAGE_KEY));
    return Array.isArray(dades) ? dades : [];
  } catch {
    return [];
  }
}

export const useComandaStore = defineStore("comanda", {
  state: () => ({
    llibres: llegirComanda(),
  }),

  getters: {
    nombreLlibres: (state) => state.llibres.length,
  },

  actions: {
    afegirLlibre(llibre) {
      if (this.llibres.some((element) => element.id === llibre.id)) {
        return false;
      }

      this.llibres.push({
        id: llibre.id,
        titol: llibre.titol,
        autor: llibre.autor,
        portada: llibre.portada ?? "",
        biblioteca: llibre.biblioteca ?? null,
      });
      sessionStorage.setItem(COMANDA_STORAGE_KEY, JSON.stringify(this.llibres));
      return true;
    },

    eliminarLlibre(id) {
      this.llibres = this.llibres.filter((llibre) => llibre.id !== id);
      sessionStorage.setItem(COMANDA_STORAGE_KEY, JSON.stringify(this.llibres));
    },

    buidar() {
      this.llibres = [];
      sessionStorage.removeItem(COMANDA_STORAGE_KEY);
    },
  },
});
