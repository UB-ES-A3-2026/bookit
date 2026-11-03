import { createApp, h, nextTick } from "vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";
import { createPinia } from "pinia";
import { afterEach, describe, expect, it } from "vitest";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";
import router from "../router";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/registre", name: "registre", component: RegisterView },
  { path: "/inicia-sessio", name: "inici-sessio", component: { render: () => null } },
];

const muntarAplicacio = async () => {
  const aplicacioRouter = createRouter({
    history: createMemoryHistory(),
    routes,
  });
  const contenidor = document.createElement("div");
  document.body.appendChild(contenidor);
  const aplicacio = createApp({ render: () => h(RouterView) });

  // La capçalera de la pàgina d'inici consulta la sessió (Pinia) per saber quins botons mostra.
  aplicacio.use(createPinia()).use(aplicacioRouter).mount(contenidor);
  await aplicacioRouter.push("/");
  await aplicacioRouter.isReady();
  await nextTick();

  return { aplicacio, aplicacioRouter, contenidor };
};

afterEach(() => {
  document.body.innerHTML = "";
});

describe("rutes publiques", () => {
  it("defineix la pàgina d'inici, la de registre i la d'inici de sessió", () => {
    const rutes = router.getRoutes().map((ruta) => ruta.path);

    expect(rutes).toEqual(expect.arrayContaining(["/", "/registre", "/inicia-sessio"]));
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
  it("mostra la marca i els enllaços de registre i d'inici de sessió", async () => {
    const aplicacio = await muntarAplicacio();

    expect(aplicacio.contenidor.textContent).toContain("bookit.");
    expect(aplicacio.contenidor.textContent).toContain("Registra't");
    expect(aplicacio.contenidor.textContent).toContain("Inicia sessió");
    expect(aplicacio.contenidor.querySelector('a[href="/registre"]')).not.toBeNull();
    expect(aplicacio.contenidor.querySelector('a[href="/inicia-sessio"]')).not.toBeNull();

    aplicacio.aplicacio.unmount();
  });
});
