import { createRouter, createWebHistory } from "vue-router";
import { useSessioStore } from "../stores/sessio.js";
import AfegirLlibreView from "../views/AfegirLlibreView.vue";
import CatalegView from "../views/CatalegView.vue";
import ComandaView from "../views/ComandaView.vue";
import HomeView from "../views/HomeView.vue";
import MevesComandesView from "../views/MevesComandesView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterConfirmationView from "../views/RegisterConfirmationView.vue";
import RegisterView from "../views/RegisterView.vue";
import RoleHomeView from "../views/RoleHomeView.vue";
import FrangesView from "../views/FrangesView.vue";
import RutaView from "../views/RutaView.vue";
import SearchView from "../views/SearchView.vue";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

// Les franges i la ruta només són per als repartidors.
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
      path: "/repartidor/ruta",
      name: "ruta-repartidor",
      component: RutaView,
      meta: { titol: "La meva ruta d'avui" },
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
  ],
});

router.afterEach((ruta) => {
  document.title = titolPestanya(ruta);
});

export default router;
