import api from "./api.js";

export async function llistaPrestecs() {
  const resposta = await api.get("/prestecs/prestecs/");
  return resposta.data;
}
