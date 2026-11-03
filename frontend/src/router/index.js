import { createRouter, createWebHistory } from "vue-router";
import CatalegView from "../views/CatalegView.vue";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/registre", name: "registre", component: RegisterView },
    { path: "/cataleg", name: "cataleg", component: CatalegView },
  ],
});
