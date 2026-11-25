import api from "./api.js";

// Notificacions de l'usuari, de la més nova a la més antiga (docs/api-comandes.md).
export async function llistaNotificacions() {
  const resposta = await api.get("/prestecs/notificacions/");
  return resposta.data;
}

export async function marcaLlegida(id) {
  const resposta = await api.post(`/prestecs/notificacions/${id}/llegida/`);
  return resposta.data;
}

export async function marcaTotesLlegides() {
  const resposta = await api.post("/prestecs/notificacions/llegides/");
  return resposta.data;
}
