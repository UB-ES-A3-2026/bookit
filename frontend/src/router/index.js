import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterConfirmationView from "../views/RegisterConfirmationView.vue";
import RegisterView from "../views/RegisterView.vue";
import RoleHomeView from "../views/RoleHomeView.vue";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

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
    { path: "/cataleg", name: "cataleg", component: RoleHomeView },
    {
      path: "/verificacio/biblioteca/:uidb64/:token",
      name: "verificacio-biblioteca",
      component: VerifyLibraryView,
    },
    {
      path: "/api/auth/verify/biblioteca/:uidb64/:token",
      name: "verificacio-biblioteca-api",
      component: VerifyLibraryView,
    },
  ],
});
