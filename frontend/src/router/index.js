import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";
import SearchView from "../views/SearchView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/registre", name: "registre", component: RegisterView },
    { path: "/cerca", name: "cerca", component: SearchView },
  ],
});
