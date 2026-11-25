// Comprovacions de format dels formularis. Només serveixen per avisar l'usuari
// abans d'enviar: la validació definitiva la fa el backend.

// Treu els espais, els guions i les barres i passa les lletres a majúscules.
function normalitza(text) {
  return text.replace(/[\s\-/]/g, "").toUpperCase();
}

// Text@domini.extensió, igual que al formulari de lector.
export function esCorreuValid(correu) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correu.trim());
}

// DNI (8 xifres i lletra) o NIE (X, Y o Z, 7 xifres i lletra). La lletra final
// ha de ser la que correspon al número.
export function esDniNieValid(dniNie) {
  const text = normalitza(dniNie);
  if (!/^[XYZ0-9][0-9]{7}[A-Z]$/.test(text)) {
    return false;
  }
  // En un NIE, la X, la Y i la Z compten com a 0, 1 i 2.
  const numero = Number(
    text.slice(0, 8).replace("X", "0").replace("Y", "1").replace("Z", "2"),
  );
  const lletres = "TRWAGMYFPDXBNJZSQVHLCKE";
  return text[8] === lletres[numero % 23];
}

// Telèfon espanyol: 9 xifres que comencen per 6, 7, 8 o 9, amb +34 opcional.
export function esTelefonValid(telefon) {
  return /^(\+34)?[6-9][0-9]{8}$/.test(normalitza(telefon));
}

// Matrícula actual: 4 xifres i 3 consonants (sense vocals, Ñ ni Q).
export function esMatriculaValida(matricula) {
  return /^[0-9]{4}[BCDFGHJKLMNPRSTVWXYZ]{3}$/.test(normalitza(matricula));
}

// Número de la Seguretat Social: 12 xifres, amb barres o espais opcionals.
export function esNumSeguretatSocialValid(numero) {
  return /^[0-9]{12}$/.test(normalitza(numero));
}

// ISBN-10 o ISBN-13 amb el dígit de control correcte, amb guions o espais o
// sense (igual que cataleg/validacions.py al backend). L'ISBN-10 pot acabar en X.
export function esIsbnValid(isbn) {
  const text = isbn.replace(/[\s-]/g, "").toUpperCase();

  if (/^[0-9]{9}[0-9X]$/.test(text)) {
    const suma = [...text].reduce(
      (total, caracter, posicio) =>
        total + (caracter === "X" ? 10 : Number(caracter)) * (10 - posicio),
      0,
    );
    return suma % 11 === 0;
  }

  if (/^97[89][0-9]{10}$/.test(text)) {
    const suma = [...text].reduce(
      (total, xifra, posicio) => total + Number(xifra) * (posicio % 2 === 0 ? 1 : 3),
      0,
    );
    return suma % 10 === 0;
  }

  return false;
}

// Enllaç http o https, com el que accepta el backend per a la portada.
export function esEnllacValid(enllac) {
  try {
    const url = new URL(enllac.trim());
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}
