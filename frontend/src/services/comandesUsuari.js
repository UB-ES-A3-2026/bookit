import api from "./api.js";

// Totes les comandes de l'usuari, de la més nova a la més antiga
// (docs/api-comandes.md).
export async function llistaMevesComandes() {
  const resposta = await api.get("/prestecs/comandes/");
  return resposta.data;
}

export async function cancellaComanda(id) {
  const resposta = await api.post(`/prestecs/comandes/${id}/cancellar/`);
  return resposta.data;
}
