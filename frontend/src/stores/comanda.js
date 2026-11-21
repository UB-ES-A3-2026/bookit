import { defineStore } from "pinia";

const ORDER_STORAGE_KEY = "bookit.comanda";

function llegirComanda() {
  const comandaDesada = sessionStorage.getItem(ORDER_STORAGE_KEY);

  if (!comandaDesada) {
    return [];
  }

  try {
    const comanda = JSON.parse(comandaDesada);
    return Array.isArray(comanda) ? comanda : [];
  } catch {
    sessionStorage.removeItem(ORDER_STORAGE_KEY);
    return [];
  }
}

function desarComanda(llibres) {
  sessionStorage.setItem(ORDER_STORAGE_KEY, JSON.stringify(llibres));
}

export const useComandaStore = defineStore("comanda", {
  state: () => ({
    llibres: llegirComanda(),
  }),

  getters: {
    nombreLlibres: (state) => state.llibres.length,
    teLlibre: (state) => (id) =>
      state.llibres.some((llibre) => llibre.id === id),
  },

  actions: {
    afegirLlibre(llibre) {
      if (this.teLlibre(llibre.id)) {
        return false;
      }

      this.llibres.push({
        id: llibre.id,
        titol: llibre.titol,
        autor: llibre.autor,
        portada: llibre.portada ?? "",
        biblioteca: llibre.biblioteca ?? null,
      });
      desarComanda(this.llibres);
      return true;
    },

    eliminarLlibre(id) {
      this.llibres = this.llibres.filter((llibre) => llibre.id !== id);
      desarComanda(this.llibres);
    },

    buidar() {
      this.llibres = [];
      sessionStorage.removeItem(ORDER_STORAGE_KEY);
    },
  },
});
