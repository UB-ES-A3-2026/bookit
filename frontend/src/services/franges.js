import api from "./api.js";

const RUTA = "/usuaris/repartidor/franges/";

export async function llistaFranges() {
  const resposta = await api.get(RUTA);
  return resposta.data.franges;
}

// Substitueix tot l'horari de la setmana (docs/api-franges.md).
export async function desaFranges(franges) {
  const resposta = await api.put(RUTA, { franges });
  return resposta.data.franges;
}
