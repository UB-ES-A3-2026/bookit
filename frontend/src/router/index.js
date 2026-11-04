import { createRouter, createWebHistory } from "vue-router";
import { useSessioStore } from "../stores/sessio.js";
import AfegirLlibreView from "../views/AfegirLlibreView.vue";
import CatalegView from "../views/CatalegView.vue";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterConfirmationView from "../views/RegisterConfirmationView.vue";
import RegisterView from "../views/RegisterView.vue";
import RoleHomeView from "../views/RoleHomeView.vue";
import SearchView from "../views/SearchView.vue";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

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

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/registre", name: "registre", component: RegisterView },
    {
      path: "/registre/confirmacio",
      name: "registre-confirmacio",
      component: RegisterConfirmationView,
    },
    { path: "/inicia-sessio", name: "inici-sessio", component: LoginView },
    {
      path: "/repartidor",
      name: "espai-repartidor",
      component: RoleHomeView,
    },
    {
      path: "/cataleg",
      name: "cataleg",
      component: CatalegView,
      beforeEnter: nomesBiblioteques,
    },
    {
      path: "/cataleg/afegir",
      name: "cataleg-afegir",
      component: AfegirLlibreView,
      beforeEnter: nomesBiblioteques,
    },
    {
      path: "/verificacio/biblioteca/:uidb64/:token",
      name: "verificacio-biblioteca",
      component: VerifyLibraryView,
    },
    { path: "/cerca", name: "cerca", component: SearchView },
  ],
});
