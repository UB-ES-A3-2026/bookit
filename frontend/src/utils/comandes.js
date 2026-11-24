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

// Dia local d'un moment ISO 8601, amb el mateix format que formataData.
export function formataDia(moment) {
  return new Date(moment).toLocaleDateString("ca-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
