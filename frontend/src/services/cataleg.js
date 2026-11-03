import api from "./api.js";

// Llibres del catàleg de la biblioteca que ha iniciat sessió (docs/api-cataleg.md).
// El client de api.js hi afegeix el token de la sessió.
export async function llistaCataleg() {
  const resposta = await api.get("/cataleg/biblioteca/llibres/");
  return resposta.data;
}
