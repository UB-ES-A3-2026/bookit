import { createRouter, createWebHistory } from "vue-router";
import { useSessioStore } from "../stores/sessio.js";
import AdrecesView from "../views/AdrecesView.vue";
import AfegirLlibreView from "../views/AfegirLlibreView.vue";
import ComandesBibliotecaView from "../views/ComandesBibliotecaView.vue";
import CatalegView from "../views/CatalegView.vue";
import ComandaView from "../views/ComandaView.vue";
import HomeView from "../views/HomeView.vue";
import LlibreDetallView from "../views/LlibreDetallView.vue";
import MevesComandesView from "../views/MevesComandesView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterConfirmationView from "../views/RegisterConfirmationView.vue";
import RegisterView from "../views/RegisterView.vue";
import RoleHomeView from "../views/RoleHomeView.vue";
import FrangesView from "../views/FrangesView.vue";
import SearchView from "../views/SearchView.vue";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

// Les franges només són per als repartidors.
export function nomesRepartidors() {
  const sessio = useSessioStore();

  if (!sessio.autenticat) {
    return { name: "inici-sessio" };
  }
  if (sessio.rol !== "repartidor") {
    return { name: "home" };
  }
  return true;
}

// El catàleg només és per a biblioteques. Sense sessió es demana iniciar-la i
// amb un altre rol es torna a l'inici.
export function nomesBiblioteques() {
  const sessio = useSessioStore();

  if (!sessio.autenticat) {
    return { name: "inici-sessio" };
  }

  if (sessio.rol !== "biblioteca") {
    return { name: "home" };
  }
  return true;
}

export function nomesUsuaris() {
  const sessio = useSessioStore();

  if (!sessio.autenticat) {
    return { name: "inici-sessio" };
  }
  if (sessio.rol !== "usuari") {
    return { name: "home" };
  }
  return true;
}

export function requereixSessio() {
  const sessio = useSessioStore();
  return sessio.autenticat ? true : { name: "inici-sessio" };
}

export const NOM_APLICACIO = "bookit";

// Text de la pestanya del navegador: el títol de la vista seguit del nom de l'aplicació.
export function titolPestanya(ruta) {
  const titol = ruta.meta?.titol;
  return titol ? `${titol} · ${NOM_APLICACIO}` : NOM_APLICACIO;
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
      meta: { titol: "Inici" },
    },
    {
      path: "/comandes",
      name: "meves-comandes",
      component: MevesComandesView,
      meta: { titol: "Les meves comandes" },
      beforeEnter: nomesUsuaris,
    },
    {
      path: "/registre",
      name: "registre",
      component: RegisterView,
      meta: { titol: "Crear un compte" },
    },
    {
      path: "/registre/confirmacio",
      name: "registre-confirmacio",
      component: RegisterConfirmationView,
      meta: { titol: "Confirmació del registre" },
    },
    {
      path: "/inicia-sessio",
      name: "inici-sessio",
      component: LoginView,
      meta: { titol: "Inicia sessió" },
    },
    {
      path: "/adreces",
      name: "adreces",
      component: AdrecesView,
      meta: { titol: "Les meves adreces" },
      beforeEnter: requereixSessio,
    },
    {
      path: "/repartidor",
      name: "espai-repartidor",
      component: RoleHomeView,
      meta: { titol: "Espai del repartidor" },
    },
    {
      path: "/repartidor/franges",
      name: "franges-repartidor",
      component: FrangesView,
      meta: { titol: "Franges de disponibilitat" },
      beforeEnter: nomesRepartidors,
    },
    {
      path: "/cataleg",
      name: "cataleg",
      component: CatalegView,
      meta: { titol: "El meu catàleg" },
      beforeEnter: nomesBiblioteques,
    },
    {
      path: "/biblioteca/comandes",
      name: "comandes-biblioteca",
      component: ComandesBibliotecaView,
      meta: { titol: "Comandes pendents" },
      beforeEnter: nomesBiblioteques,
    },
    {
      path: "/cataleg/afegir",
      name: "cataleg-afegir",
      component: AfegirLlibreView,
      meta: { titol: "Afegir un llibre" },
      beforeEnter: nomesBiblioteques,
    },
    {
      path: "/comanda",
      name: "comanda",
      component: ComandaView,
      meta: { titol: "La meva comanda" },
      beforeEnter: nomesUsuaris,
    },
    {
      path: "/verificacio/biblioteca/:uidb64/:token",
      name: "verificacio-biblioteca",
      component: VerifyLibraryView,
      meta: { titol: "Verificació del compte" },
    },
    {
      path: "/cerca",
      name: "cerca",
      component: SearchView,
      meta: { titol: "Resultats de la cerca" },
    },
    {
      path: "/llibres/:id",
      name: "detall-llibre",
      component: LlibreDetallView,
      meta: { titol: "Detall del llibre" },
    },
  ],
});

router.afterEach((ruta) => {
  document.title = titolPestanya(ruta);
});

export default router;
