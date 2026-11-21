import api from "./api.js";

export async function confirmaComanda(dades) {
  const resposta = await api.post("/prestecs/comandes/", dades);
  return resposta.data;
}
