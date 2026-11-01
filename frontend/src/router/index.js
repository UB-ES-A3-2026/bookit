import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";
import VerifyLibraryView from "../views/VerifyLibraryView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/registre", name: "registre", component: RegisterView },
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
