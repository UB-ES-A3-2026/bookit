import api from "./api.js";

export async function llistaBibliotequesAmbEstoc(llibreId) {
  const resposta = await api.get(
    `/cataleg/llibres/${llibreId}/biblioteques/`,
  );
  return resposta.data;
}

export async function apuntaLlistaEspera(llibreId) {
  const resposta = await api.post(
    `/cataleg/llibres/${llibreId}/llista-espera/`,
  );
  return { data: resposta.data, status: resposta.status };
}
