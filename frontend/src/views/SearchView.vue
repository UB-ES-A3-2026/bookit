<script setup>
import axios from "axios";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const route = useRoute();
const router = useRouter();
const sessio = useSessioStore();
const comanda = useComandaStore();

// El text cercat i la pàgina arriben a l'adreça (/cerca?q=...&pagina=2).
const textCercat = computed(() => (route.query.q ?? "").trim());
const pagina = computed(() => Number(route.query.pagina) || 1);

const resultats = ref([]);
const total = ref(0);
const hiHaSeguent = ref(false);
const hiHaAnterior = ref(false);
const carregant = ref(false);
const error = ref("");
const apuntatsEspera = ref([]);

const textTotal = computed(() =>
  total.value === 1 ? "1 resultat" : `${total.value} resultats`,
);

function textValoracions(llibre) {
  if (!llibre.nombre_valoracions) {
    return "Sense valoracions";
  }
  const mitjana = llibre.mitjana_valoracions.toLocaleString("ca", {
    maximumFractionDigits: 1,
  });
  const valoracions =
    llibre.nombre_valoracions === 1
      ? "1 valoració"
      : `${llibre.nombre_valoracions} valoracions`;
  return `${mitjana} de 5 · ${valoracions}`;
}

async function cerca() {
  resultats.value = [];
  total.value = 0;
  hiHaSeguent.value = false;
  hiHaAnterior.value = false;
  error.value = "";

  if (!textCercat.value) {
    return;
  }

  carregant.value = true;
  try {
    const resposta = await axios.get(`${apiUrl}/api/cataleg/llibres/`, {
      params: { q: textCercat.value, page: pagina.value },
    });
    resultats.value = resposta.data.results;
    total.value = resposta.data.count;
    hiHaSeguent.value = Boolean(resposta.data.next);
    hiHaAnterior.value = Boolean(resposta.data.previous);
  } catch {
    error.value = "No s'ha pogut fer la cerca. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

function canviaPagina(novaPagina) {
  router.push({ name: "cerca", query: { q: textCercat.value, pagina: novaPagina } });
}

function afegeixALaComanda(llibre) {
  if (!sessio.autenticat) {
    router.push({ name: "inici-sessio" });
    return;
  }

  comanda.afegirLlibre(llibre);
}

function apuntaAEspera(llibre) {
  if (!apuntatsEspera.value.includes(llibre.id)) {
    apuntatsEspera.value.push(llibre.id);
  }
}

// Torna a cercar quan canvia el text o la pàgina de l'adreça.
watch(() => [textCercat.value, pagina.value], cerca, { immediate: true });
</script>

<template>
  <main class="search-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <div class="header-actions">
        <RouterLink v-if="sessio.rol === 'usuari'" class="order-link" :to="{ name: 'comanda' }">
          La meva comanda ({{ comanda.nombreLlibres }})
        </RouterLink>
        <RouterLink class="back-link" to="/">Torna a l'inici</RouterLink>
      </div>
    </header>

    <section class="search-content">
      <p class="eyebrow">Cerca de llibres</p>
      <h1>Resultats de la cerca</h1>
      <p v-if="textCercat" class="description">
        Has cercat «{{ textCercat }}».
        <span v-if="!carregant && !error && total > 0">{{ textTotal }}.</span>
      </p>
      <p v-else class="description">
        Escriu el títol, l'autor o l'ISBN al cercador de la pàgina d'inici.
      </p>

      <p v-if="carregant" class="estat" role="status">Cercant llibres...</p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="cerca">
          Tornar-ho a provar
        </button>
      </div>

      <template v-else-if="resultats.length > 0">
        <ul class="llista-resultats" aria-label="Resultats de la cerca">
          <li v-for="llibre in resultats" :key="llibre.id" class="llibre">
            <img
              v-if="llibre.portada"
              class="portada"
              :src="llibre.portada"
              :alt="`Portada de ${llibre.titol}`"
            />
            <div v-else class="portada portada-per-defecte" aria-hidden="true">
              <span>{{ llibre.titol }}</span>
            </div>

            <div class="dades-llibre">
              <h2>{{ llibre.titol }}</h2>
              <p class="autor">{{ llibre.autor }}</p>
              <p
                class="disponibilitat"
                :class="{ 'no-disponible': !llibre.disponible }"
              >
                {{ llibre.disponible ? "Disponible" : "No disponible" }}
              </p>
              <p class="valoracions">{{ textValoracions(llibre) }}</p>
              <p v-if="!llibre.disponible" class="stock-warning" role="alert">
                Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera
                <button
                  type="button"
                  class="wait-button"
                  :disabled="apuntatsEspera.includes(llibre.id)"
                  @click="apuntaAEspera(llibre)"
                >
                  {{
                    apuntatsEspera.includes(llibre.id)
                      ? "Apuntat a la llista d'espera"
                      : "Apuntar-me a la llista d'espera"
                  }}
                </button>
              </p>
              <button
                type="button"
                class="add-button"
                :disabled="!llibre.disponible || comanda.teLlibre(llibre.id)"
                @click="afegeixALaComanda(llibre)"
              >
                {{
                  comanda.teLlibre(llibre.id)
                    ? "Afegit a la comanda"
                    : llibre.disponible
                      ? "Afegir a la comanda"
                      : "No disponible"
                }}
              </button>
            </div>
          </li>
        </ul>

        <nav
          v-if="hiHaAnterior || hiHaSeguent"
          class="paginacio"
          aria-label="Pàgines de resultats"
        >
          <button
            type="button"
            class="secondary-button"
            :disabled="!hiHaAnterior"
            @click="canviaPagina(pagina - 1)"
          >
            Anterior
          </button>
          <span>Pàgina {{ pagina }}</span>
          <button
            type="button"
            class="secondary-button"
            :disabled="!hiHaSeguent"
            @click="canviaPagina(pagina + 1)"
          >
            Següent
          </button>
        </nav>
      </template>

      <p v-else-if="textCercat" class="estat sense-resultats">
        No s'ha trobat el llibre cercat, assegura't que l'informació introduïda
        sigui correcta
      </p>
    </section>
  </main>
</template>

<style scoped>
.search-page {
  min-height: 100svh;
  color: #241914;
  background: #f9f4eb;
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

.back-link {
  color: #a00000;
  font-weight: 700;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.order-link {
  color: #a00000;
  font-weight: 700;
}

.search-content {
  max-width: 1170px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: #a00000;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.eyebrow::before {
  display: inline-block;
  width: 1.25rem;
  margin: 0 0.7rem 0.2rem 0;
  border-top: 1px solid currentColor;
  content: "";
}

h1 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2rem, 4vw, 2.6rem);
  letter-spacing: -0.03em;
}

.description {
  margin: 0.75rem 0 2rem;
  color: #4d4541;
}

.estat {
  padding: 1.5rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  color: #4d4541;
  background: #fffdf8;
}

.sense-resultats {
  color: #241914;
  font-weight: 700;
}

.estat-error {
  color: #870000;
}

.estat-error p {
  margin: 0 0 1rem;
}

.secondary-button {
  padding: 0.6rem 1.1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.55rem;
  color: #241914;
  background: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button:disabled {
  color: #b5aaa0;
  cursor: default;
}

.llista-resultats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 1.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.llibre {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding: 0.9rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.9rem;
  background: #fffdf8;
}

.portada {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 0.4rem;
  object-fit: cover;
}

.portada-per-defecte {
  display: grid;
  place-items: center;
  padding: 1rem;
  box-sizing: border-box;
  color: #fffdf8;
  background: linear-gradient(160deg, #a00000, #5c0000);
  font-family: Georgia, serif;
  font-size: 1.15rem;
  font-weight: 700;
  text-align: center;
}

.dades-llibre h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.1rem;
}

.dades-llibre p {
  margin: 0.3rem 0 0;
  font-size: 0.9rem;
}

.autor {
  color: #4d4541;
}

.disponibilitat {
  color: #1f7a3d;
  font-weight: 700;
}

.disponibilitat::before {
  display: inline-block;
  width: 0.5rem;
  height: 0.5rem;
  margin-right: 0.4rem;
  border-radius: 50%;
  background: currentColor;
  content: "";
}

.no-disponible {
  color: #92867c;
}

.valoracions {
  color: #92867c;
}

.stock-warning {
  margin: 0.7rem 0 0;
  padding: 0.55rem;
  border: 1px solid #dfc0b0;
  border-radius: 0.45rem;
  color: #870000;
  background: #fff1e8;
  font-size: 0.78rem;
  font-weight: 700;
}

.wait-button {
  display: block;
  margin-top: 0.5rem;
  padding: 0.45rem 0.7rem;
  border: 1px solid #870000;
  border-radius: 0.45rem;
  color: #870000;
  background: #fff;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.wait-button:disabled {
  color: #68705f;
  border-color: #9da48f;
  cursor: default;
}

.add-button {
  width: 100%;
  margin-top: 0.7rem;
  padding: 0.6rem 0.8rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
}

.add-button:hover:not(:disabled) {
  background: #720000;
}

.add-button:disabled {
  color: #887b70;
  background: #e8dfd3;
  cursor: default;
}

.paginacio {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
  color: #4d4541;
}
</style>
