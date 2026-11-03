import api from "./api.js";

// Llibres del catàleg de la biblioteca que ha iniciat sessió (docs/api-cataleg.md).
// El client de api.js hi afegeix el token de la sessió.
export async function llistaCataleg() {
  const resposta = await api.get("/cataleg/biblioteca/llibres/");
  return resposta.data;
}

export async function editaLlibre(id, dades) {
  const resposta = await api.patch(`/cataleg/biblioteca/llibres/${id}/`, dades);
  return resposta.data;
}

export async function actualitzaExemplars(id, exemplars) {
  const resposta = await api.patch(
    `/cataleg/biblioteca/llibres/${id}/exemplars/`,
    { exemplars },
  );
  return resposta.data;
}

export async function retiraLlibre(id) {
  await api.delete(`/cataleg/biblioteca/llibres/${id}/`);
}
