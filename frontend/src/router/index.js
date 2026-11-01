import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import RegisterConfirmationView from "../views/RegisterConfirmationView.vue";
import RegisterView from "../views/RegisterView.vue";

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
  ],
});
