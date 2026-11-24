import { defineStore } from "pinia";
import { useSessioStore } from "./sessio.js";

const PREFIX_CLAU = "bookit.comanda";
export const LIMIT_LLIBRES_COMANDA = 5;

// Cada usuari té la seva comanda, desada al localStorage perquè no es perdi si es
// tanca la pestanya i perquè un altre usuari del mateix navegador no la vegi.
function clauComanda() {
  const usuari = useSessioStore().usuari;
  return usuari?.id ? `${PREFIX_CLAU}.${usuari.id}` : PREFIX_CLAU;
}

function llegirComanda(clau) {
  try {
    const comanda = JSON.parse(localStorage.getItem(clau));
    return Array.isArray(comanda) ? comanda : [];
  } catch {
    localStorage.removeItem(clau);
    return [];
  }
}

export const useComandaStore = defineStore("comanda", {
  state: () => {
    const clau = clauComanda();
    return { clau, llibres: llegirComanda(clau) };
  },

  getters: {
    nombreLlibres: (state) => state.llibres.length,
    superaLimit: (state) => state.llibres.length > LIMIT_LLIBRES_COMANDA,
    teLlibre: (state) => (id) =>
      state.llibres.some((llibre) => llibre.id === id),
    // Una comanda és d'una sola biblioteca: la dels llibres que ja hi ha.
    biblioteca: (state) => state.llibres[0]?.biblioteca ?? null,
  },

  actions: {
    // Torna a llegir la comanda si ha canviat l'usuari de la sessió.
    sincronitza() {
      const clau = clauComanda();
      if (clau !== this.clau) {
        this.clau = clau;
        this.llibres = llegirComanda(clau);
      }
    },

    desa() {
      localStorage.setItem(this.clau, JSON.stringify(this.llibres));
    },

    // Diu si el llibre es pot afegir des d'aquesta biblioteca.
    esDUnaAltraBiblioteca(biblioteca) {
      this.sincronitza();
      return this.biblioteca !== null && this.biblioteca.id !== biblioteca?.id;
    },

    afegirLlibre(llibre) {
      this.sincronitza();
      if (!llibre.biblioteca || this.teLlibre(llibre.id) || this.esDUnaAltraBiblioteca(llibre.biblioteca)) {
        return false;
      }

      this.llibres.push({
        id: llibre.id,
        titol: llibre.titol,
        autor: llibre.autor,
        portada: llibre.portada ?? "",
        biblioteca: { id: llibre.biblioteca.id, nom: llibre.biblioteca.nom },
      });
      this.desa();
      return true;
    },

    eliminarLlibre(id) {
      this.sincronitza();
      this.llibres = this.llibres.filter((llibre) => llibre.id !== id);
      this.desa();
    },

    buidar() {
      this.sincronitza();
      this.llibres = [];
      localStorage.removeItem(this.clau);
    },
  },
});
