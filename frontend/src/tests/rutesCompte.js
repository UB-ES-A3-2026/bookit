// Rutes buides per als tests que munten pàgines amb sessió: la capçalera i la
// barra lateral del compte hi enllacen pel nom, i el router les ha de conèixer.
const buida = { template: "<p />" };

export const rutesCompte = [
  { path: "/", name: "home", component: buida },
  { path: "/cerca", name: "cerca", component: buida },
  { path: "/comandes", name: "meves-comandes", component: buida },
  { path: "/comanda", name: "comanda", component: buida },
  { path: "/prestecs", name: "prestecs", component: buida },
  { path: "/adreces", name: "adreces", component: buida },
  // L'enllaç principal de la capçalera de les biblioteques i dels repartidors.
  { path: "/cataleg", name: "cataleg", component: buida },
  { path: "/repartidor/ruta", name: "ruta-repartidor", component: buida },
];

// Afegeix les rutes del compte que la llista encara no tingui.
export function ambRutesCompte(rutes) {
  const noms = new Set(rutes.map((ruta) => ruta.name));
  return [...rutes, ...rutesCompte.filter((ruta) => !noms.has(ruta.name))];
}
