import axios from "axios";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Llibres del catàleg de la biblioteca que ha iniciat sessió (docs/api-cataleg.md).
// Quan la US2 arribi a develop, aquesta petició ha de passar pel client de
// services/api.js, que hi afegeix el token de la sessió.
export async function llistaCataleg() {
  const resposta = await axios.get(`${apiUrl}/api/cataleg/biblioteca/llibres/`);
  return resposta.data;
}
