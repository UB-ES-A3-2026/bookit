import api from "./api.js";

// Parades de la ruta d'avui del repartidor, ja ordenades pel camp `ordre`
// (docs/api-repartidor.md). Si avui no té ruta, la llista és buida.
export async function llistaRutaAvui() {
  const resposta = await api.get("/prestecs/repartidor/ruta-avui/");
  return resposta.data;
}

// Marca una parada com a completada (US13-T1). Retorna la parada actualitzada.
export async function completaParada(id) {
  const resposta = await api.post(`/prestecs/repartidor/parades/${id}/completar/`);
  return resposta.data;
}

// Marca una parada com a fallida amb el motiu obligatori (US13-T2).
export async function fallaParada(id, motiu) {
  const resposta = await api.post(`/prestecs/repartidor/parades/${id}/fallida/`, { motiu });
  return resposta.data;
}
