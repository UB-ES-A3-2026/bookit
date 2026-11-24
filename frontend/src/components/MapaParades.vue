<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Mapa base estàndard de l'Institut Cartogràfic i Geològic de Catalunya (ICGC).
const URL_MAPA_BASE =
  "https://geoserveis.icgc.cat/servei/catalunya/mapa-base/wmts/estandard/MON3857NW/{z}/{x}/{y}.png";
const ATRIBUCIO =
  '© <a href="https://www.icgc.cat/" target="_blank" rel="noopener">Institut Cartogràfic i Geològic de Catalunya</a>';
// Zoom màxim en ajustar el mapa a les parades, perquè una sola parada no
// quedi massa a prop.
const ZOOM_MAXIM_AJUST = 16;

const props = defineProps({
  // Parades de la ruta en l'ordre en què s'han de fer.
  parades: { type: Array, required: true },
  // Text de la ubicació de cada parada, el mateix que es mostra a la llista.
  llocDe: { type: Function, required: true },
  // Noms dels tipus de parada ("Recollida", "Lliurament").
  tipus: { type: Object, required: true },
});

const contenidor = ref(null);
let mapa = null;
let capaParades = null;

function coordenada(valor) {
  // L'API pot enviar els decimals com a número o com a text.
  if (valor === null || valor === undefined || valor === "") {
    return null;
  }
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : null;
}

// Parades amb ubicació coneguda, que són les úniques que es poden situar.
const paradesAmbUbicacio = computed(() =>
  props.parades
    .map((parada) => ({
      parada,
      latitud: coordenada(parada.adreca?.latitud),
      longitud: coordenada(parada.adreca?.longitud),
    }))
    .filter(({ latitud, longitud }) => latitud !== null && longitud !== null),
);

const senseUbicacio = computed(() => props.parades.length - paradesAmbUbicacio.value.length);

const avis = computed(() => {
  if (props.parades.length === 0 || senseUbicacio.value === 0) {
    return "";
  }
  if (paradesAmbUbicacio.value.length === 0) {
    return "Encara no tenim la ubicació de cap parada, per això no es pot mostrar el mapa. Les tens totes a la llista.";
  }
  return senseUbicacio.value === 1
    ? "1 parada no surt al mapa perquè no en tenim la ubicació. La tens a la llista."
    : `${senseUbicacio.value} parades no surten al mapa perquè no en tenim la ubicació. Les tens a la llista.`;
});

function nomTipus(parada) {
  return props.tipus[parada.tipus] ?? parada.tipus;
}

function llistaOrdres(parades) {
  const ordres = parades.map((parada) => String(parada.ordre));
  return ordres.length === 1
    ? ordres[0]
    : `${ordres.slice(0, -1).join(", ")} i ${ordres.at(-1)}`;
}

// Parades que són al mateix lloc (per exemple, diverses recollides a la mateixa
// biblioteca) en un sol grup, perquè els marcadors no quedin l'un sobre l'altre.
const grups = computed(() => {
  const perLloc = new Map();
  for (const punt of paradesAmbUbicacio.value) {
    const clau = `${punt.latitud.toFixed(6)},${punt.longitud.toFixed(6)}`;
    if (!perLloc.has(clau)) {
      perLloc.set(clau, { latitud: punt.latitud, longitud: punt.longitud, parades: [] });
    }
    perLloc.get(clau).parades.push(punt.parada);
  }
  return [...perLloc.values()];
});

// El contingut de la finestra es construeix amb nodes de text perquè l'adreça
// l'escriu l'usuari i no s'ha d'interpretar com a HTML.
function contingutFinestra(parades) {
  const element = document.createElement("div");
  parades.forEach((parada, index) => {
    if (index > 0) {
      element.append(document.createElement("br"));
    }
    const titol = document.createElement("strong");
    titol.textContent = `${parada.ordre}. ${nomTipus(parada)}`;
    const lloc = document.createElement("span");
    lloc.textContent = ` · ${props.llocDe(parada)}`;
    element.append(titol, lloc);
  });
  return element;
}

function marcador({ parades, latitud, longitud }) {
  const tipus = [...new Set(parades.map((parada) => parada.tipus))];
  const unSolTipus = tipus.length === 1;
  const amplada = 32 + (parades.length - 1) * 22;
  const icona = L.divIcon({
    className: `marcador-parada marcador-${unSolTipus ? tipus[0] : "mixt"}`,
    html: `<span>${parades.map((parada) => Number(parada.ordre)).join(" · ")}</span>`,
    iconSize: [amplada, 32],
    iconAnchor: [amplada / 2, 16],
    popupAnchor: [0, -16],
  });
  const nom = parades.length === 1 ? "Parada" : "Parades";
  const descripcio = unSolTipus ? `: ${nomTipus(parades[0])}` : "";
  return L.marker([latitud, longitud], {
    icon: icona,
    title: `${nom} ${llistaOrdres(parades)}${descripcio}`,
    alt: `${nom} ${llistaOrdres(parades)}`,
  }).bindPopup(contingutFinestra(parades));
}

function dibuixaParades() {
  capaParades.clearLayers();
  const punts = paradesAmbUbicacio.value;
  if (punts.length === 0) {
    return;
  }

  // El recorregut uneix les parades en ordre.
  if (punts.length > 1) {
    L.polyline(
      punts.map(({ latitud, longitud }) => [latitud, longitud]),
      { color: "#6b5d52", weight: 3, opacity: 0.7, dashArray: "6 8", interactive: false },
    ).addTo(capaParades);
  }
  grups.value.forEach((grup) => marcador(grup).addTo(capaParades));

  mapa.fitBounds(
    L.latLngBounds(punts.map(({ latitud, longitud }) => [latitud, longitud])),
    { padding: [32, 32], maxZoom: ZOOM_MAXIM_AJUST },
  );
}

function creaMapa() {
  mapa = L.map(contenidor.value, { scrollWheelZoom: false });
  L.tileLayer(URL_MAPA_BASE, { attribution: ATRIBUCIO, maxZoom: 19 }).addTo(mapa);
  capaParades = L.layerGroup().addTo(mapa);
}

function destrueixMapa() {
  mapa?.remove();
  mapa = null;
  capaParades = null;
}

// El contenidor només existeix quan hi ha alguna parada amb ubicació; el mapa
// es crea, s'actualitza o es destrueix quan canvien les parades.
watch(
  paradesAmbUbicacio,
  async (punts) => {
    await nextTick();
    if (punts.length === 0 || !contenidor.value) {
      destrueixMapa();
      return;
    }
    if (!mapa) {
      creaMapa();
    }
    dibuixaParades();
  },
  { immediate: true, flush: "post" },
);

onBeforeUnmount(destrueixMapa);
</script>

<template>
  <section v-if="parades.length" class="mapa-parades" aria-label="Mapa de la ruta">
    <div
      v-if="paradesAmbUbicacio.length"
      ref="contenidor"
      class="mapa"
      data-testid="mapa-parades"
      role="region"
      aria-label="Mapa amb les parades de la ruta d'avui"
    ></div>
    <p v-if="avis" class="avis-mapa" role="note">{{ avis }}</p>
  </section>
</template>

<style scoped>
.mapa-parades {
  margin: 0 0 1.5rem;
}

.mapa {
  height: clamp(260px, 45vh, 420px);
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  overflow: hidden;
  /* Leaflet fa servir z-index alts: es limiten al mapa perquè no tapin la capçalera. */
  isolation: isolate;
}

.avis-mapa {
  margin: 0.75rem 0 0;
  padding: 0.75rem 1rem;
  border: 1px solid #e6d3a8;
  border-radius: 0.55rem;
  color: #5c4a1f;
  background: #fbf3df;
  font-size: 0.9rem;
}

/* Les icones les crea Leaflet fora de l'abast dels estils amb scope. */
:deep(.marcador-parada) {
  display: grid;
  border: 2px solid #fff;
  border-radius: 999px;
  place-items: center;
  color: #fff;
  background: #980000;
  box-shadow: 0 1px 4px rgb(0 0 0 / 35%);
  font-weight: 800;
}

:deep(.marcador-lliurament) {
  background: #1d5a36;
}

/* Recollides i lliuraments al mateix lloc. */
:deep(.marcador-mixt) {
  background: #6b5d52;
}
</style>
