import api from "./api.js";

const RUTA_ADRECES = "/usuaris/adreces/";

export async function llistaAdreces() {
  const resposta = await api.get(RUTA_ADRECES);
  return resposta.data;
}

export async function afegeixAdreca(dades) {
  const resposta = await api.post(RUTA_ADRECES, dades);
  return resposta.data;
}

export async function editaAdreca(id, dades) {
  const resposta = await api.patch(`${RUTA_ADRECES}${id}/`, dades);
  return resposta.data;
}

export async function marcaAdrecaPredeterminada(id) {
  const resposta = await api.post(`${RUTA_ADRECES}${id}/predeterminada/`, {});
  return resposta.data;
}

export async function suprimeixAdreca(id) {
  await api.delete(`${RUTA_ADRECES}${id}/`);
}
