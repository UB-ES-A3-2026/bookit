import api from "./api.js";

// Afegeix un llibre al catàleg de la biblioteca i en retorna les dades desades.
export async function afegeixLlibre(dades) {
  const resposta = await api.post("/cataleg/biblioteca/llibres/", dades);
  return resposta.data;
}

// Llibres del catàleg de la biblioteca que ha iniciat sessió (docs/api-cataleg.md).
// El client de api.js hi afegeix el token de la sessió.
export async function llistaCataleg() {
  const resposta = await api.get("/cataleg/biblioteca/llibres/");
  return resposta.data;
}
