import api from "./api.js";

// Parades de la ruta d'avui del repartidor, ja ordenades pel camp `ordre`
// (docs/api-repartidor.md). Si avui no té ruta, la llista és buida.
export async function llistaRutaAvui() {
  const resposta = await api.get("/prestecs/repartidor/ruta-avui/");
  return resposta.data;
}
