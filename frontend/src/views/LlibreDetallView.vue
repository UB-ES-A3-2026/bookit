<script setup>
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import {
  apuntaLlistaEspera,
  llistaBibliotequesAmbEstoc,
} from "../services/biblioteques.js";
import { useSessioStore } from "../stores/sessio.js";

const route = useRoute();
const sessio = useSessioStore();

function valorQuery(valor, perDefecte = "") {
  return typeof valor === "string" ? valor : perDefecte;
}

const llibreId = computed(() => Number(route.params.id));
const titol = computed(() => valorQuery(route.query.titol, "Detall del llibre"));
const autor = computed(() => valorQuery(route.query.autor));
const portada = computed(() => valorQuery(route.query.portada));
const cercaAnterior = computed(() => valorQuery(route.query.cerca));
const paginaAnterior = computed(() => valorQuery(route.query.pagina));
const rutaResultats = computed(() => ({
  name: "cerca",
  query: cercaAnterior.value
    ? { q: cercaAnterior.value, pagina: paginaAnterior.value || "1" }
    : {},
}));

const disponibilitat = ref(null);
const carregant = ref(true);
const error = ref("");
const errorLlistaEspera = ref("");
const missatgeLlistaEspera = ref("");
const apuntantLlistaEspera = ref(false);
const llistaEsperaCompletada = ref(false);

const biblioteques = computed(
  () => disponibilitat.value?.biblioteques ?? [],
);
const senseEstoc = computed(
  () => disponibilitat.value !== null && biblioteques.value.length === 0,
);

function textDistancia(distancia) {
  return `${Number(distancia).toLocaleString("ca", {
    maximumFractionDigits: 1,
  })} km`;
}

function textExemplars(quantitat) {
  return quantitat === 1 ? "1 exemplar disponible" : `${quantitat} exemplars disponibles`;
}

async function carregaDisponibilitat() {
  const id = llibreId.value;
  disponibilitat.value = null;
  error.value = "";

  if (!Number.isSafeInteger(id) || id < 1) {
    error.value = "No s'ha pogut trobar aquest llibre.";
    carregant.value = false;
    return;
  }

  carregant.value = true;
  try {
    const resposta = await llistaBibliotequesAmbEstoc(id);
    if (!Array.isArray(resposta.biblioteques)) {
      throw new Error("La resposta de disponibilitat no conté la llista de biblioteques.");
    }
    disponibilitat.value = resposta;
  } catch {
    error.value =
      "No s'ha pogut carregar la disponibilitat del llibre. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

async function apuntaEspera() {
  if (!sessio.autenticat || apuntantLlistaEspera.value) {
    return;
  }

  apuntantLlistaEspera.value = true;
  errorLlistaEspera.value = "";
  missatgeLlistaEspera.value = "";

  try {
    const resposta = await apuntaLlistaEspera(llibreId.value);
    if (resposta.status === 201) {
      missatgeLlistaEspera.value =
        "T'has apuntat a la llista d'espera d'aquest llibre.";
    } else if (resposta.status === 200) {
      missatgeLlistaEspera.value =
        "Ja estaves apuntat a la llista d'espera d'aquest llibre.";
    } else {
      throw new Error("La resposta de la llista d'espera no és vàlida.");
    }
    llistaEsperaCompletada.value = true;
  } catch (errorPeticio) {
    errorLlistaEspera.value =
      errorPeticio.response?.data?.detail ??
      "No s'ha pogut actualitzar la llista d'espera. Torna-ho a provar.";
  } finally {
    apuntantLlistaEspera.value = false;
  }
}

watch(llibreId, carregaDisponibilitat, { immediate: true });
</script>

<template>
  <main class="book-detail-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>
      <RouterLink class="back-link" :to="rutaResultats">
        Torna als resultats
      </RouterLink>
    </header>

    <section class="detail-content">
      <nav class="breadcrumb" aria-label="Ruta de navegació">
        <RouterLink :to="rutaResultats">Resultats de la cerca</RouterLink>
        <span aria-hidden="true">/</span>
        <span>Detall del llibre</span>
      </nav>

      <section class="book-summary" aria-labelledby="book-title">
        <img v-if="portada" class="book-cover" :src="portada" :alt="`Portada de ${titol}`" />
        <div v-else class="book-cover book-cover--empty" aria-hidden="true">
          {{ titol }}
        </div>
        <div class="book-information">
          <p class="eyebrow">Disponibilitat a les biblioteques</p>
          <h1 id="book-title">{{ titol }}</h1>
          <p v-if="autor" class="book-author">{{ autor }}</p>
          <p class="book-description">
            Consulta quines biblioteques tenen aquest llibre disponible.
          </p>
        </div>
      </section>

      <section class="availability-section" aria-labelledby="availability-title">
        <div class="availability-heading">
          <div>
            <h2 id="availability-title">Biblioteques amb estoc</h2>
            <p v-if="disponibilitat?.ordenada_per_distancia">
              Ordenades per distància a la teva adreça predeterminada.
            </p>
          </div>
          <span v-if="!carregant && !error && biblioteques.length" class="library-count">
            {{ biblioteques.length }}
            {{ biblioteques.length === 1 ? "biblioteca" : "biblioteques" }}
          </span>
        </div>

        <p v-if="carregant" class="page-state" role="status">
          Carregant biblioteques...
        </p>
        <div v-else-if="error" class="page-state page-error" role="alert">
          <p>{{ error }}</p>
          <button type="button" class="secondary-button" @click="carregaDisponibilitat">
            Tornar-ho a provar
          </button>
        </div>
        <template v-else-if="disponibilitat">
          <p
            v-if="disponibilitat.missatge"
            class="availability-message"
            :class="{ 'availability-message--empty': senseEstoc }"
            role="status"
          >
            {{ disponibilitat.missatge }}
          </p>

          <ul
            v-if="biblioteques.length"
            class="library-list"
            aria-label="Biblioteques que tenen el llibre en estoc"
          >
            <li
              v-for="biblioteca in biblioteques"
              :key="biblioteca.id"
              class="library-card"
            >
              <span class="library-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M3 20h18M5 20V9l7-5 7 5v11M9 20v-6h6v6M8 10h.01M16 10h.01" />
                </svg>
              </span>
              <div class="library-information">
                <h3>{{ biblioteca.nom }}</h3>
                <p>{{ biblioteca.carrer }} {{ biblioteca.numero_porta }}</p>
                <p class="stock-count">{{ textExemplars(biblioteca.exemplars) }}</p>
              </div>
              <span
                v-if="
                  disponibilitat.ordenada_per_distancia &&
                  biblioteca.distancia_km !== undefined
                "
                class="distance"
              >
                {{ textDistancia(biblioteca.distancia_km) }}
              </span>
            </li>
          </ul>

          <p v-else-if="!disponibilitat.missatge" class="availability-message">
            No hi ha biblioteques amb estoc disponible.
          </p>

          <aside class="waitlist-panel">
            <div class="waitlist-icon" aria-hidden="true">↗</div>
            <div class="waitlist-copy">
              <strong>No trobes una biblioteca que et vagi bé?</strong>
              <p>Pots apuntar-te a la llista d'espera d'aquest llibre.</p>
            </div>
            <button
              v-if="sessio.autenticat"
              type="button"
              class="primary-button"
              :disabled="apuntantLlistaEspera || llistaEsperaCompletada"
              @click="apuntaEspera"
            >
              {{
                apuntantLlistaEspera
                  ? "Apuntant..."
                  : llistaEsperaCompletada
                    ? "Sol·licitud registrada"
                    : "Llista d'espera"
              }}
            </button>
            <RouterLink v-else class="primary-button" to="/inicia-sessio">
              Inicia sessió
            </RouterLink>
          </aside>
          <p v-if="missatgeLlistaEspera" class="waitlist-success" role="status">
            {{ missatgeLlistaEspera }}
          </p>
          <p v-if="errorLlistaEspera" class="waitlist-error" role="alert">
            {{ errorLlistaEspera }}
          </p>
        </template>
      </section>
    </section>
  </main>
</template>

<style scoped>
.book-detail-page {
  min-height: 100svh;
  color: #241914;
  background: #f5ecdc;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 62px;
  padding: 0 max(1.25rem, calc((100% - 1170px) / 2));
  background: #fffdf9;
  box-sizing: border-box;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: #271d1a;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  text-decoration: none;
}

.brand-mark {
  display: block;
  width: 2rem;
  height: 2rem;
  border-radius: 0.35rem;
  background-position: center 36%;
  background-size: auto 240%;
}

.back-link,
.breadcrumb a {
  color: #870000;
  font-size: 0.85rem;
  font-weight: 700;
  text-decoration: none;
}

.detail-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
  color: #817569;
  font-size: 0.72rem;
}

.book-summary {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr);
  align-items: center;
  gap: 1.75rem;
  padding: 1.4rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.85rem;
  background: #fffdf8;
}

.book-cover {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 0.45rem;
  object-fit: cover;
  box-shadow: 0 0.5rem 1rem rgb(36 25 20 / 14%);
}

.book-cover--empty {
  display: grid;
  padding: 0.8rem;
  box-sizing: border-box;
  place-items: center;
  color: #fffdf8;
  background: linear-gradient(160deg, #a00000, #5c0000);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1rem;
  font-weight: 700;
  text-align: center;
}

.eyebrow {
  margin: 0 0 0.5rem;
  color: #a00000;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
}

h1 {
  font-size: clamp(1.8rem, 3.5vw, 2.5rem);
  line-height: 1.15;
}

.book-author {
  margin-top: 0.55rem;
  color: #4d4541;
  font-size: 1rem;
}

.book-description {
  margin-top: 1rem;
  color: #6b5d52;
  font-size: 0.9rem;
}

.availability-section {
  margin-top: 2rem;
}

.availability-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.availability-heading h2 {
  font-size: 1.5rem;
}

.availability-heading p {
  margin-top: 0.3rem;
  color: #6b5d52;
  font-size: 0.8rem;
}

.library-count {
  color: #6b5d52;
  font-size: 0.8rem;
}

.page-state,
.availability-message {
  padding: 1rem 1.1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.65rem;
  color: #4d4541;
  background: #fffdf8;
}

.page-error,
.availability-message--empty,
.waitlist-error {
  color: #870000;
}

.page-error p {
  margin-bottom: 0.8rem;
}

.availability-message {
  margin-bottom: 0.85rem;
  font-weight: 700;
}

.availability-message--empty {
  background: #fbeaea;
}

.library-list {
  display: grid;
  gap: 0.65rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.library-card {
  display: grid;
  grid-template-columns: 2.5rem minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.65rem;
  background: #fffdf8;
}

.library-icon {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  place-items: center;
  border-radius: 0.55rem;
  color: #870000;
  background: #f4e5c9;
}

.library-icon svg {
  width: 1.3rem;
  height: 1.3rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.library-information h3 {
  font-size: 1.05rem;
}

.library-information p {
  margin-top: 0.25rem;
  color: #6b5d52;
  font-size: 0.82rem;
}

.library-information .stock-count {
  color: #277347;
  font-weight: 700;
}

.distance {
  padding: 0.35rem 0.55rem;
  border-radius: 99px;
  color: #355f4b;
  background: #e6f4ed;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.waitlist-panel {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  margin-top: 1rem;
  border-radius: 0.65rem;
  background: #f2e5c8;
}

.waitlist-icon {
  display: grid;
  flex: 0 0 2.2rem;
  height: 2.2rem;
  place-items: center;
  border-radius: 50%;
  color: #870000;
  background: #fff8e9;
  font-size: 1.2rem;
}

.waitlist-copy {
  flex: 1;
}

.waitlist-copy strong {
  font-size: 0.85rem;
}

.waitlist-copy p {
  margin-top: 0.2rem;
  color: #6b5d52;
  font-size: 0.75rem;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 0.9rem;
  border: 0;
  border-radius: 0.5rem;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

.primary-button {
  color: #fff;
  background: #980000;
}

.primary-button:hover,
.primary-button:focus-visible {
  background: #720000;
}

.primary-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.secondary-button {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.waitlist-success,
.waitlist-error {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: #e6f4ed;
  font-size: 0.85rem;
}

.waitlist-error {
  background: #fbeaea;
}

@media (max-width: 600px) {
  .detail-content {
    padding-top: 1.25rem;
  }

  .book-summary {
    grid-template-columns: 95px minmax(0, 1fr);
    gap: 1rem;
    padding: 1rem;
  }

  .availability-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .library-card {
    grid-template-columns: 2.2rem minmax(0, 1fr);
    padding: 0.85rem;
  }

  .distance {
    grid-column: 2;
    justify-self: start;
  }

  .waitlist-panel {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .waitlist-copy {
    flex-basis: calc(100% - 3.2rem);
  }

  .waitlist-panel .primary-button {
    width: 100%;
  }
}
</style>
