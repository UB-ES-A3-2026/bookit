import { createApp, h, nextTick } from "vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";
import { afterEach, describe, expect, it } from "vitest";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";
import router from "../router";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/registre", name: "registre", component: RegisterView },
];

const muntarAplicacio = async () => {
  const aplicacioRouter = createRouter({
    history: createMemoryHistory(),
    routes,
  });
  const contenidor = document.createElement("div");
  document.body.appendChild(contenidor);
  const aplicacio = createApp({ render: () => h(RouterView) });

  aplicacio.use(aplicacioRouter).mount(contenidor);
  await aplicacioRouter.push("/");
  await aplicacioRouter.isReady();
  await nextTick();

  return { aplicacio, aplicacioRouter, contenidor };
};

afterEach(() => {
  document.body.innerHTML = "";
});

describe("rutes publiques", () => {
  it("defineix la pàgina d'inici i la de registre", () => {
    expect(router.getRoutes().map((ruta) => ruta.path)).toEqual(["/", "/registre"]);
  });

  it("permet navegar entre l'inici i el registre", async () => {
    const aplicacio = await muntarAplicacio();

    await aplicacio.aplicacioRouter.push("/registre");
    expect(aplicacio.aplicacioRouter.currentRoute.value.path).toBe("/registre");

    await aplicacio.aplicacioRouter.push("/");
    expect(aplicacio.aplicacioRouter.currentRoute.value.path).toBe("/");

    aplicacio.aplicacio.unmount();
  });
});

describe("pàgina d'inici", () => {
  it("mostra la marca i l'enllaç de registre", async () => {
    const aplicacio = await muntarAplicacio();

    expect(aplicacio.contenidor.textContent).toContain("bookit.");
    expect(aplicacio.contenidor.textContent).toContain("Registra't");
    expect(aplicacio.contenidor.querySelector('a[href="/registre"]')).not.toBeNull();

    aplicacio.aplicacio.unmount();
  });
});
