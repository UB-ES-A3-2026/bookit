import api from "./api.js";

// Comandes pendents de la biblioteca, ja ordenades per data de lliurament
// (docs/api-comandes.md).
export async function llistaComandesBiblioteca() {
  const resposta = await api.get("/prestecs/biblioteca/comandes/");
  return resposta.data;
}

// Marca una comanda com a "Llesta per a recollida" (estat `preparada`) i
// retorna la comanda actualitzada (docs/api-comandes.md).
export async function marcaComandaPreparada(id) {
  const resposta = await api.post(`/prestecs/biblioteca/comandes/${id}/preparada/`);
  return resposta.data;
}

// Marca com a lliurada una comanda de recollida quan l'usuari la ve a buscar i
// retorna la comanda actualitzada (US7-T8, docs/api-comandes.md).
export async function lliuraComandaRecollida(id) {
  const resposta = await api.post(`/prestecs/biblioteca/comandes/${id}/recollida/`);
  return resposta.data;
}
