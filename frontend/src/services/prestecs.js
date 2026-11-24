import api from "./api.js";

export async function obtenirCostosLliurament() {
  const resposta = await api.get("/prestecs/comandes/cost-enviament/");
  return resposta.data;
}

export async function confirmaComanda(dades) {
  const resposta = await api.post("/prestecs/comandes/", dades);
  return resposta.data;
}
