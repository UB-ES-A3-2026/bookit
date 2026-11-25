import { createApp, h, nextTick } from "vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, describe, expect, it } from "vitest";
import HomeView from "../views/HomeView.vue";
import RegisterView from "../views/RegisterView.vue";
import router, { requereixSessio } from "../router";
import { useSessioStore } from "../stores/sessio.js";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/registre", name: "registre", component: RegisterView },
  { path: "/inicia-sessio", name: "inici-sessio", component: { render: () => null } },
  { path: "/adreces", name: "adreces", component: { render: () => null } },
  // La capçalera amb sessió també enllaça a les comandes de l'usuari (US8).
  { path: "/comandes", name: "meves-comandes", component: { render: () => null } },
  // I als préstecs de l'usuari (US19).
  { path: "/prestecs", name: "prestecs", component: { render: () => null } },
  // El menú de l'usuari també porta a la cistella.
  { path: "/comanda", name: "comanda", component: { render: () => null } },
];

const muntarAplicacio = async (autenticada = false) => {
  const aplicacioRouter = createRouter({
    history: createMemoryHistory(),
    routes,
  });
  const contenidor = document.createElement("div");
  document.body.appendChild(contenidor);
  const aplicacio = createApp({ render: () => h(RouterView) });
  const pinia = createPinia();
  setActivePinia(pinia);
  if (autenticada) {
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });
  }

  // La capçalera de la pàgina d'inici consulta la sessió (Pinia) per saber quins botons mostra.
  aplicacio.use(pinia).use(aplicacioRouter).mount(contenidor);
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

  it("mostra l'enllaç a les adreces dins del menú de l'usuari quan hi ha una sessió", async () => {
    const aplicacio = await muntarAplicacio(true);

    // Amb el menú tancat la capçalera només mostra el botó amb el nom.
    expect(aplicacio.contenidor.querySelector('a[href="/adreces"]')).toBeNull();

    aplicacio.contenidor.querySelector(".menu-usuari__boto").click();
    await nextTick();

    expect(
      aplicacio.contenidor.querySelector('a[href="/adreces"]')?.textContent,
    ).toContain("Les meves adreces");

    aplicacio.aplicacio.unmount();
  });
});

describe("accés a les adreces", () => {
  it("demana iniciar sessió si no hi ha cap usuari autenticat", () => {
    setActivePinia(createPinia());

    expect(requereixSessio()).toEqual({ name: "inici-sessio" });
  });

  it("permet accedir-hi amb una sessió autenticada", () => {
    setActivePinia(createPinia());
    useSessioStore().iniciarSessio({ accessToken: "token-de-prova", rol: "usuari" });

    expect(requereixSessio()).toBe(true);
  });

  it("defineix la ruta privada i el títol de la pàgina", () => {
    const adreces = router.getRoutes().find((ruta) => ruta.name === "adreces");

    expect(adreces.path).toBe("/adreces");
    expect(adreces.meta.titol).toBe("Les meves adreces");
    expect(adreces.beforeEnter).toBe(requereixSessio);
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
