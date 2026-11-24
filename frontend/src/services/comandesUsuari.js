import api from "./api.js";

// Totes les comandes de l'usuari, de la més nova a la més antiga
// (docs/api-comandes.md).
export async function llistaMevesComandes() {
  const resposta = await api.get("/prestecs/comandes/");
  return resposta.data;
}
