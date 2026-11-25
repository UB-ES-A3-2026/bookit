<script setup>
import { computed, onMounted, onUnmounted, ref, useId, watch } from "vue";
import { useSessioStore } from "../stores/sessio.js";
import {
  llistaNotificacions,
  marcaLlegida,
  marcaTotesLlegides,
} from "../services/notificacions.js";

const sessio = useSessioStore();
const esUsuari = computed(() => sessio.autenticat && sessio.rol === "usuari");

const idPanell = useId();
const arrel = ref(null);
const boto = ref(null);
const obert = ref(false);
const notificacions = ref([]);
const carregant = ref(false);
const desant = ref(false);
const errorCarrega = ref("");
const errorAccio = ref("");

const noves = computed(() =>
  Array.isArray(notificacions.value)
    ? notificacions.value.filter((notificacio) => !notificacio.llegida).length
    : 0,
);

// Puja a cada càrrega i a cada canvi. Així es descarta una resposta antiga que
// arriba tard: desfaria una lectura o mostraria dades d'una sessió tancada.
let versio = 0;

async function carrega() {
  const versioPeticio = ++versio;
  carregant.value = true;
  errorCarrega.value = "";

  try {
    const dades = await llistaNotificacions();
    if (versioPeticio === versio) {
      notificacions.value = dades;
    }
  } catch {
    if (versioPeticio === versio) {
      errorCarrega.value = "No s'han pogut carregar les notificacions.";
    }
  } finally {
    if (versioPeticio === versio) {
      carregant.value = false;
    }
  }
}

async function desaLectura(peticio, aplicaCanvi) {
  const versioPeticio = ++versio;
  carregant.value = false;
  desant.value = true;
  errorAccio.value = "";

  try {
    await peticio();
    if (versioPeticio === versio) {
      aplicaCanvi();
    }
  } catch {
    if (versioPeticio === versio) {
      errorAccio.value = "No s'ha pogut desar la lectura. Torna-ho a provar.";
    }
  } finally {
    desant.value = false;
  }
}

function llegeix(notificacio) {
  return desaLectura(
    () => marcaLlegida(notificacio.id),
    () => {
      notificacio.llegida = true;
    },
  );
}

// Després de marcar-les totes es torna a demanar la llista: el servidor també
// marca les que hagin arribat des de l'última càrrega. Abans es marquen aquí,
// perquè ja estan desades encara que la recàrrega falli.
function llegeixTotes() {
  return desaLectura(marcaTotesLlegides, () => {
    notificacions.value.forEach((notificacio) => {
      notificacio.llegida = true;
    });
    carrega();
  });
}

function commuta() {
  obert.value = !obert.value;
  if (obert.value && !desant.value) {
    errorAccio.value = "";
    carrega();
  }
}

function tanca() {
  obert.value = false;
  boto.value?.focus();
}

function tancaSiEsClicaFora(event) {
  // composedPath i no contains: el botó clicat pot haver sortit ja del DOM.
  if (obert.value && !event.composedPath().includes(arrel.value)) {
    obert.value = false;
  }
}

function formataMoment(moment) {
  return new Date(moment).toLocaleString("ca-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// La capçalera no es torna a muntar quan es tanca la sessió des de l'inici.
watch(esUsuari, (ara) => {
  versio += 1;
  obert.value = false;
  notificacions.value = [];
  if (ara) {
    carrega();
  }
});

onMounted(() => {
  document.addEventListener("click", tancaSiEsClicaFora);
  if (esUsuari.value) {
    carrega();
  }
});

onUnmounted(() => {
  document.removeEventListener("click", tancaSiEsClicaFora);
});
</script>

<template>
  <div v-if="esUsuari" ref="arrel" class="notificacions" @keydown.esc="tanca">
    <button
      ref="boto"
      type="button"
      class="notificacions-boto"
      :aria-expanded="obert"
      :aria-controls="idPanell"
      @click="commuta"
    >
      <svg class="campaneta" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </svg>
      <span class="nomes-lector">Notificacions</span>
      <span v-if="noves" class="comptador">
        {{ noves
        }}<span class="nomes-lector">{{
          noves === 1 ? " nova" : " noves"
        }}</span>
      </span>
    </button>

    <section
      v-show="obert"
      :id="idPanell"
      class="panell"
      aria-label="Llista de notificacions"
    >
      <p v-if="errorAccio" class="error error-accio" role="alert">
        {{ errorAccio }}
      </p>

      <div v-if="errorCarrega" class="error error-carrega" role="alert">
        <p>{{ errorCarrega }}</p>
        <button type="button" class="accio reintenta" @click="carrega">
          Tornar-ho a provar
        </button>
      </div>
      <p
        v-else-if="carregant && !notificacions.length"
        class="buit"
        role="status"
      >
        Carregant les notificacions...
      </p>
      <p v-else-if="!notificacions.length" class="buit">
        No tens cap notificació.
      </p>

      <template v-if="notificacions.length">
        <button
          v-if="noves"
          type="button"
          class="accio llegeix-totes"
          :disabled="desant"
          @click="llegeixTotes"
        >
          Marcar-les totes com a llegides
        </button>

        <ul class="llista">
          <li
            v-for="notificacio in notificacions"
            :key="notificacio.id"
            class="notificacio"
            :class="{ nova: !notificacio.llegida }"
          >
            <p class="text">{{ notificacio.text }}</p>
            <p class="detall">
              Comanda {{ notificacio.comanda }} ·
              {{ formataMoment(notificacio.creada) }}
            </p>
            <button
              v-if="!notificacio.llegida"
              type="button"
              class="accio llegeix"
              :disabled="desant"
              @click="llegeix(notificacio)"
            >
              Marcar com a llegida
            </button>
          </li>
        </ul>
      </template>
    </section>
  </div>
</template>

<style scoped>
.notificacions {
  position: relative;
}

.notificacions-boto {
  position: relative;
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  border: 1px solid #e4d8cc;
  border-radius: 50%;
  color: #241914;
  background: #fffdf9;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.notificacions-boto:hover,
.notificacions-boto[aria-expanded="true"] {
  border-color: #c9b6a4;
  box-shadow: 0 0.2rem 0.6rem rgb(60 30 10 / 10%);
}

.notificacions-boto:focus-visible {
  outline: 3px solid #ffbf47;
  outline-offset: 2px;
}

.campaneta {
  width: 1.2rem;
  height: 1.2rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

/* El nombre de notificacions noves surt com una bombolla sobre la campaneta. */
.comptador {
  position: absolute;
  top: -0.3rem;
  right: -0.3rem;
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.25rem;
  border: 2px solid #fffdf9;
  border-radius: 999px;
  color: #fff;
  background: #980000;
  font-size: 0.65rem;
  font-weight: 800;
  line-height: 1.15rem;
  text-align: center;
  box-sizing: content-box;
}

.nomes-lector {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.panell {
  position: absolute;
  z-index: 10;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 22rem;
  max-height: 70vh;
  padding: 0.9rem;
  overflow-y: auto;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  color: #241914;
  background: #fffdf8;
  box-shadow: 0 1rem 2rem rgb(72 0 0 / 15%);
  box-sizing: border-box;
  text-align: left;
}

.llista {
  margin: 0;
  padding: 0;
  list-style: none;
}

.notificacio {
  padding: 0.75rem;
  border-bottom: 1px solid #efe5d6;
  font-size: 0.85rem;
  line-height: 1.4;
}

.notificacio.nova {
  background: #f9f0e2;
  font-weight: 700;
}

.detall,
.buit {
  color: #6b5d52;
  font-size: 0.8rem;
}

.detall {
  margin-top: 0.25rem;
  font-weight: 400;
}

.error {
  color: #870000;
  font-size: 0.85rem;
}

.accio {
  margin: 0.4rem 0;
  padding: 0;
  border: 0;
  color: #980000;
  background: none;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
}

.accio:disabled {
  cursor: wait;
  opacity: 0.5;
}

@media (max-width: 700px) {
  .notificacions {
    position: static;
  }

  /* Amb top automàtic queda just sota el botó, ocupi el que ocupi la capçalera. */
  .panell {
    top: auto;
    margin-top: 0.5rem;
    right: 0.75rem;
    left: 0.75rem;
    width: auto;
  }
}
</style>
