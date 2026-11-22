import api from "./api.js";

// Comandes pendents de la biblioteca, ja ordenades per data de lliurament
// (docs/api-comandes.md).
export async function llistaComandesBiblioteca() {
  const resposta = await api.get("/prestecs/biblioteca/comandes/");
  return resposta.data;
}
