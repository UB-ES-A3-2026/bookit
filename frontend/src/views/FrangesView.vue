<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { useSessioStore } from "../stores/sessio.js";
import { desaFranges, llistaFranges } from "../services/franges.js";

const DIES = ["Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabte", "Diumenge"];

const router = useRouter();
const sessio = useSessioStore();

const franges = ref([]);
const desades = ref("[]");
const carregant = ref(true);
const desant = ref(false);
const errorCarrega = ref("");
const errorDesar = ref("");
const errorsFranja = ref({});
const missatge = ref("");

// Les franges noves encara no tenen id: cal una clau pròpia per a la llista.
let seguentClau = 0;

function senseClaus() {
  return franges.value.map(({ dia, hora_inici, hora_fi }) => ({ dia, hora_inici, hora_fi }));
}

const hiHaCanvis = computed(() => JSON.stringify(senseClaus()) !== desades.value);

function posaFranges(dades) {
  franges.value = dades.map(({ dia, hora_inici, hora_fi }) => ({
    clau: seguentClau++,
    dia,
    hora_inici,
    hora_fi,
  }));
  desades.value = JSON.stringify(senseClaus());
}

function frangesDelDia(dia) {
  return franges.value.filter((franja) => franja.dia === dia);
}

function netejaAvisos() {
  errorDesar.value = "";
  errorsFranja.value = {};
  missatge.value = "";
}

function afegeixFranja(dia) {
  franges.value.push({ clau: seguentClau++, dia, hora_inici: "", hora_fi: "" });
  netejaAvisos();
}

function treuFranja(franja) {
  franges.value = franges.value.filter((element) => element.clau !== franja.clau);
  netejaAvisos();
}

function tancaSessio() {
  sessio.tancarSessio();
  router.push({ name: "home" });
}

async function carregaFranges() {
  carregant.value = true;
  errorCarrega.value = "";

  try {
    posaFranges(await llistaFranges());
  } catch (error) {
    // Només els repartidors validats tenen franges.
    if (error.response?.status === 403) {
      router.push({ name: "home" });
      return;
    }
    errorCarrega.value =
      "No s'han pogut carregar les teves franges. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

// El 400 porta una llista de missatges generals o bé un objecte amb els errors
// de cada franja segons la posició en què s'ha enviat.
function mostraErrors(error) {
  const detall = error.response?.status === 400 ? error.response.data?.franges : null;

  if (Array.isArray(detall)) {
    errorDesar.value = detall.join(" ");
  } else if (detall && typeof detall === "object") {
    const perClau = {};
    Object.entries(detall).forEach(([posicio, camps]) => {
      const franja = franges.value[Number(posicio)];
      if (franja) {
        perClau[franja.clau] = Object.values(camps).flat();
      }
    });
    errorsFranja.value = perClau;
    errorDesar.value = "Revisa les franges marcades. No s'ha desat cap canvi.";
  } else {
    errorDesar.value = "No s'han pogut desar les franges. Torna-ho a provar.";
  }
}

async function desa() {
  netejaAvisos();
  desant.value = true;

  try {
    posaFranges(await desaFranges(senseClaus()));
    missatge.value = "S'han desat les teves franges.";
  } catch (error) {
    mostraErrors(error);
  } finally {
    desant.value = false;
  }
}

onMounted(carregaFranges);
</script>

<template>
  <main class="franges-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <div class="header-accions">
        <RouterLink class="header-link" :to="{ name: 'espai-repartidor' }">
          El meu espai
        </RouterLink>
        <button type="button" class="logout-button" @click="tancaSessio">
          Tancar sessió
        </button>
      </div>
    </header>

    <section class="franges-content">
      <p class="eyebrow">Espai de repartidor</p>
      <h1>Franges de disponibilitat</h1>
      <p class="description">
        Tria quan pots treballar. L'horari es repeteix cada setmana i només
        rebràs comandes que hi càpiguen.
      </p>

      <p v-if="carregant" class="estat" role="status">Carregant les franges...</p>

      <div v-else-if="errorCarrega" class="estat estat-error" role="alert">
        <p>{{ errorCarrega }}</p>
        <button type="button" class="secondary-button" @click="carregaFranges">
          Tornar-ho a provar
        </button>
      </div>

      <!-- Sense les franges carregades no hi ha formulari: desar esborraria l'horari. -->
      <form v-else novalidate @submit.prevent="desa" @input="netejaAvisos">
        <fieldset class="horari" :disabled="desant">
          <legend class="nomes-lector">Horari de la setmana</legend>

          <section v-for="(nom, dia) in DIES" :key="dia" class="dia">
            <div class="dia-capcalera">
              <h2>{{ nom }}</h2>
              <button
                type="button"
                class="secondary-button afegeix"
                :aria-label="`Afegir una franja el ${nom.toLowerCase()}`"
                @click="afegeixFranja(dia)"
              >
                Afegir una franja
              </button>
            </div>

            <p v-if="!frangesDelDia(dia).length" class="dia-buit">No disponible</p>

            <div v-for="franja in frangesDelDia(dia)" :key="franja.clau" class="franja">
              <label>
                De
                <input
                  v-model="franja.hora_inici"
                  type="time"
                  :aria-label="`Hora d'inici, ${nom.toLowerCase()}`"
                  :aria-invalid="Boolean(errorsFranja[franja.clau])"
                  :aria-describedby="errorsFranja[franja.clau] ? `error-franja-${franja.clau}` : undefined"
                />
              </label>
              <label>
                a
                <input
                  v-model="franja.hora_fi"
                  type="time"
                  :aria-label="`Hora de final, ${nom.toLowerCase()}`"
                  :aria-invalid="Boolean(errorsFranja[franja.clau])"
                  :aria-describedby="errorsFranja[franja.clau] ? `error-franja-${franja.clau}` : undefined"
                />
              </label>
              <button
                type="button"
                class="treu"
                :aria-label="`Treure la franja del ${nom.toLowerCase()}`"
                @click="treuFranja(franja)"
              >
                Treure
              </button>
              <p
                v-if="errorsFranja[franja.clau]"
                :id="`error-franja-${franja.clau}`"
                class="error-franja"
              >
                {{ errorsFranja[franja.clau].join(" ") }}
              </p>
            </div>
          </section>
        </fieldset>

        <p v-if="errorDesar" class="avis avis-error" role="alert">{{ errorDesar }}</p>
        <p v-else-if="missatge" class="avis avis-correcte" role="status">{{ missatge }}</p>
        <p v-else-if="hiHaCanvis" class="avis">Tens canvis sense desar.</p>

        <button type="submit" class="desa" :disabled="desant || !hiHaCanvis">
          {{ desant ? "Desant..." : "Desar les franges" }}
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.franges-page {
  min-height: 100svh;
  color: #241914;
  background: #f5ecdc;
}

.site-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  min-height: 62px;
  padding: 0.5rem max(1.25rem, calc((100% - 1170px) / 2));
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

.header-accions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 1.25rem;
}

.header-link {
  color: #241914;
  font-weight: 700;
}

.logout-button {
  padding: 0.55rem 1rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.logout-button:hover,
.logout-button:focus-visible {
  background: #740000;
}

.franges-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 3.5rem 1.25rem;
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: #a00000;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.2rem, 4vw, 2.8rem);
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.description {
  max-width: 34rem;
  margin: 0.75rem 0 2rem;
  color: #4d4541;
  line-height: 1.6;
}

.estat {
  padding: 1.5rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  color: #4d4541;
  background: #fffdf8;
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

.horari {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.nomes-lector {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.dia {
  margin-bottom: 0.75rem;
  padding: 1rem 1.25rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.dia-capcalera,
.franja {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
}

.dia-capcalera {
  justify-content: space-between;
}

.dia h2 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.1rem;
  font-weight: 700;
}

.afegeix {
  padding: 0.35rem 0.6rem;
  font-size: 0.8rem;
}

.dia-buit {
  color: #6b5d52;
  font-size: 0.85rem;
}

.franja {
  margin-top: 0.75rem;
}

.franja label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.franja input {
  padding: 0.4rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.4rem;
  font: inherit;
}

.franja input[aria-invalid="true"] {
  border-color: #870000;
}

.treu {
  border: 0;
  color: #870000;
  background: none;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.error-franja {
  flex-basis: 100%;
  color: #870000;
  font-size: 0.85rem;
}

.avis {
  margin: 1rem 0;
  color: #4d4541;
}

.avis-error {
  color: #870000;
}

.avis-correcte {
  color: #1d5a36;
}

.desa {
  margin-top: 1rem;
  padding: 0.75rem 1.3rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.desa:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
