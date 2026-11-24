const ESTATS = {
  rebuda: "Rebuda",
  preparada: "Preparada",
  en_cami: "En camí",
  lliurada: "Lliurada",
  cancellada: "Cancel·lada",
};

// Text que es mostra per a cada estat de docs/api-comandes.md.
export function textEstat(estat) {
  return ESTATS[estat] ?? estat;
}

// Una data sense hora (AAAA-MM-DD) no passa per Date: segons el fus horari
// sortiria el dia abans.
export function formataData(data) {
  const [any, mes, dia] = data.split("-");
  return `${dia}/${mes}/${any}`;
}

// Quan es lliura la comanda. Les de recollida no tenen data perquè no les porta
// cap repartidor: l'usuari les recull a la biblioteca (US14-T10).
export function textLliurament(comanda) {
  if (comanda.data_lliurament) {
    return formataData(comanda.data_lliurament);
  }
  return comanda.tipus_lliurament === "recollida" ? "Recollida a la biblioteca" : "Sense data";
}

// Dia local d'un moment ISO 8601, amb el mateix format que formataData.
export function formataDia(moment) {
  return new Date(moment).toLocaleDateString("ca-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
