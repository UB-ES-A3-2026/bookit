<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import {
  afegeixAdreca,
  editaAdreca,
  llistaAdreces,
  suprimeixAdreca,
} from "../services/adreces.js";
import { useSessioStore } from "../stores/sessio.js";

const router = useRouter();
const sessio = useSessioStore();

const camps = ["municipi", "carrer", "pis", "codi_postal"];
const etiquetesCamps = {
  municipi: "Municipi",
  carrer: "Carrer i número",
  pis: "Pis, porta o escala",
  codi_postal: "Codi postal",
};
const autocompletatCamps = {
  municipi: "address-level2",
  carrer: "address-line1",
  pis: "address-line2",
  codi_postal: "postal-code",
};
const campsObligatoris = "Aquest camp és obligatori.";
const adreces = ref([]);
const carregant = ref(true);
const error = ref("");
const errorAccio = ref("");
const errorGeneral = ref("");
const formulariObert = ref(false);
const editantId = ref(null);
const enviant = ref(false);
const eliminantId = ref(null);

const formulari = reactive({
  municipi: "",
  carrer: "",
  pis: "",
  codi_postal: "",
});

const errors = reactive({
  municipi: "",
  carrer: "",
  pis: "",
  codi_postal: "",
});

function netejaErrors() {
  camps.forEach((camp) => {
    errors[camp] = "";
  });
  errorGeneral.value = "";
}

function netejaFormulari() {
  camps.forEach((camp) => {
    formulari[camp] = "";
  });
  netejaErrors();
}

function iniciaNovaAdreca() {
  netejaFormulari();
  editantId.value = null;
  formulariObert.value = true;
}

function iniciaEdicio(adreca) {
  netejaErrors();
  Object.assign(formulari, {
    municipi: adreca.municipi,
    carrer: adreca.carrer,
    pis: adreca.pis,
    codi_postal: adreca.codi_postal,
  });
  editantId.value = adreca.id;
  formulariObert.value = true;
}

function cancelLaEdicio() {
  formulariObert.value = false;
  editantId.value = null;
  netejaFormulari();
}

function validaFormulari() {
  netejaErrors();
  camps.forEach((camp) => {
    if (!formulari[camp].trim()) {
      errors[camp] = campsObligatoris;
    }
  });
  return camps.every((camp) => !errors[camp]);
}

function mostraErrorsBackend(dades) {
  let teErrors = false;

  Object.entries(dades).forEach(([camp, missatges]) => {
    if (camp in errors && Array.isArray(missatges)) {
      errors[camp] = missatges.join(" ");
      teErrors = true;
    }
  });

  if (typeof dades.detail === "string") {
    errorGeneral.value = dades.detail;
    teErrors = true;
  }

  if (!teErrors) {
    errorGeneral.value =
      "No s'han pogut desar les dades de l'adreça. Torna-ho a provar.";
  }
}

async function desaAdreca() {
  errorAccio.value = "";
  if (!validaFormulari()) {
    return;
  }

  const dades = Object.fromEntries(
    camps.map((camp) => [camp, formulari[camp].trim()]),
  );
  enviant.value = true;

  try {
    if (editantId.value === null) {
      const novaAdreca = await afegeixAdreca(dades);
      adreces.value = [...adreces.value, novaAdreca].sort(
        (a, b) => a.id - b.id,
      );
    } else {
      const adrecaActualitzada = await editaAdreca(editantId.value, dades);
      const index = adreces.value.findIndex(
        (adreca) => adreca.id === editantId.value,
      );
      if (index !== -1) {
        adreces.value[index] = adrecaActualitzada;
      }
    }
    cancelLaEdicio();
  } catch (errorPeticio) {
    if (errorPeticio.response?.status === 400 && errorPeticio.response.data) {
      mostraErrorsBackend(errorPeticio.response.data);
    } else {
      errorGeneral.value =
        "No s'han pogut desar les dades de l'adreça. Torna-ho a provar més tard.";
    }
  } finally {
    enviant.value = false;
  }
}

async function confirmaSupressio(adreca) {
  if (!window.confirm(`Vols suprimir l'adreça «${adreca.carrer}»?`)) {
    return;
  }

  eliminantId.value = adreca.id;
  errorAccio.value = "";
  try {
    await suprimeixAdreca(adreca.id);
    adreces.value = adreces.value.filter((element) => element.id !== adreca.id);
    if (editantId.value === adreca.id) {
      cancelLaEdicio();
    }
  } catch {
    errorAccio.value =
      "No s'ha pogut suprimir l'adreça. Torna-ho a provar més tard.";
  } finally {
    eliminantId.value = null;
  }
}

async function carregaAdreces() {
  carregant.value = true;
  error.value = "";
  try {
    adreces.value = await llistaAdreces();
  } catch {
    error.value = "No s'han pogut carregar les adreces. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

function tancaSessio() {
  sessio.tancarSessio();
  router.push({ name: "home" });
}

onMounted(carregaAdreces);
</script>

<template>
  <main class="adreces-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <nav class="header-actions" aria-label="Navegació del compte">
        <RouterLink class="header-link" to="/">Inici</RouterLink>
        <button type="button" class="logout-button" @click="tancaSessio">
          Tancar sessió
        </button>
      </nav>
    </header>

    <section class="adreces-content">
      <div class="page-heading">
        <div>
          <p class="eyebrow">El teu compte</p>
          <h1>Les meves adreces</h1>
          <p class="description">
            Desa les adreces on vols rebre les teves comandes.
          </p>
        </div>
        <button
          v-if="!formulariObert"
          type="button"
          class="primary-button"
          @click="iniciaNovaAdreca"
        >
          Afegir una adreça
          <span aria-hidden="true">+</span>
        </button>
      </div>

      <form
        v-if="formulariObert"
        class="address-form"
        novalidate
        @submit.prevent="desaAdreca"
      >
        <div class="form-heading">
          <div>
            <h2>{{ editantId === null ? "Nova adreça" : "Editar adreça" }}</h2>
            <p>Tots els camps són obligatoris.</p>
          </div>
        </div>

        <p v-if="errorGeneral" class="form-error-general" role="alert">
          {{ errorGeneral }}
        </p>

        <div class="form-grid">
          <div v-for="camp in camps" :key="camp" class="form-field">
            <label :for="`adreca-${camp}`">
              {{ etiquetesCamps[camp] }}
            </label>
            <input
              :id="`adreca-${camp}`"
              v-model="formulari[camp]"
              type="text"
              :inputmode="camp === 'codi_postal' ? 'numeric' : undefined"
              :autocomplete="autocompletatCamps[camp]"
              :aria-invalid="Boolean(errors[camp])"
              :aria-describedby="`adreca-${camp}-error`"
              required
              @input="errors[camp] = ''"
            />
            <p
              :id="`adreca-${camp}-error`"
              class="field-error"
              aria-live="polite"
            >
              {{ errors[camp] }}
            </p>
          </div>
        </div>

        <div class="form-actions">
          <button
            type="button"
            class="secondary-button"
            :disabled="enviant"
            @click="cancelLaEdicio"
          >
            Cancel·lar
          </button>
          <button type="submit" class="primary-button" :disabled="enviant">
            {{ enviant ? "Desant..." : editantId === null ? "Afegir adreça" : "Desar canvis" }}
          </button>
        </div>
      </form>

      <p v-if="errorAccio" class="action-error" role="alert">
        {{ errorAccio }}
      </p>

      <p v-if="carregant" class="page-state" role="status">
        Carregant les adreces...
      </p>
      <div v-else-if="error" class="page-state page-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaAdreces">
          Tornar-ho a provar
        </button>
      </div>
      <p v-else-if="adreces.length === 0" class="page-state">
        Encara no tens cap adreça desada.
      </p>

      <ul
        v-if="!carregant && !error && adreces.length > 0"
        class="address-list"
        aria-label="Adreces de lliurament"
      >
        <li v-for="adreca in adreces" :key="adreca.id" class="address-card">
          <div class="address-details">
            <div class="address-title">
              <h2>{{ adreca.carrer }}</h2>
              <span v-if="adreca.predeterminada" class="default-badge">
                Predeterminada
              </span>
            </div>
            <address>
              {{ adreca.pis }}<br />
              {{ adreca.codi_postal }} {{ adreca.municipi }}
            </address>
          </div>
          <div class="address-actions">
            <button
              type="button"
              class="secondary-button"
              :aria-label="`Editar l'adreça de ${adreca.carrer}`"
              :disabled="enviant || eliminantId !== null"
              @click="iniciaEdicio(adreca)"
            >
              Editar
            </button>
            <button
              type="button"
              class="danger-button"
              :aria-label="`Suprimir l'adreça de ${adreca.carrer}`"
              :disabled="enviant || eliminantId !== null"
              @click="confirmaSupressio(adreca)"
            >
              {{ eliminantId === adreca.id ? "Suprimint..." : "Suprimir" }}
            </button>
          </div>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.adreces-page {
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

.header-actions,
.address-actions,
.form-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-link {
  color: #241914;
  font-weight: 700;
  text-decoration: none;
}

.logout-button,
.primary-button,
.secondary-button,
.danger-button {
  padding: 0.7rem 1rem;
  border: 0;
  border-radius: 0.55rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.logout-button,
.primary-button {
  color: #fff;
  background: #980000;
}

.logout-button:hover,
.primary-button:hover,
.logout-button:focus-visible,
.primary-button:focus-visible {
  background: #720000;
}

.secondary-button {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.danger-button {
  color: #870000;
  background: #fbeaea;
}

.logout-button:disabled,
.primary-button:disabled,
.secondary-button:disabled,
.danger-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.adreces-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
}

.page-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.75rem;
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
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.2rem, 4vw, 2.8rem);
  letter-spacing: -0.03em;
}

.description {
  margin-top: 0.75rem;
  color: #4d4541;
  line-height: 1.6;
}

.address-form,
.address-card,
.page-state {
  border: 1px solid #dfd1bd;
  border-radius: 0.85rem;
  background: #fffdf8;
  box-shadow: 0 0.5rem 1.5rem rgb(72 40 20 / 6%);
}

.address-form {
  padding: 1.5rem;
  margin-bottom: 1.25rem;
}

.form-heading {
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #dfd1bd;
}

.form-heading h2,
.address-title h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
}

.form-heading p {
  margin-top: 0.3rem;
  color: #6b5d52;
  font-size: 0.85rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.25rem 1rem;
}

.form-field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
  font-weight: 700;
}

.form-field input {
  width: 100%;
  padding: 0.75rem 0.85rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.5rem;
  box-sizing: border-box;
  color: #241914;
  background: #fff;
  font: inherit;
}

.form-field input:focus {
  outline: 2px solid #a00000;
  outline-offset: 1px;
}

.form-field input[aria-invalid="true"] {
  border-color: #a00000;
}

.field-error {
  min-height: 1.1rem;
  margin: 0.25rem 0 0.5rem;
  color: #870000;
  font-size: 0.8rem;
}

.form-error-general,
.action-error {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 0.55rem;
  color: #870000;
  background: #fbeaea;
  font-size: 0.9rem;
}

.form-actions {
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.page-state {
  padding: 1.25rem;
  color: #4d4541;
}

.page-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  color: #870000;
}

.address-list {
  display: grid;
  gap: 0.8rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.address-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.25rem 1.5rem;
}

.address-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.address-details address {
  margin-top: 0.45rem;
  color: #4d4541;
  font-size: 0.9rem;
  font-style: normal;
  line-height: 1.5;
}

.default-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 99px;
  color: #6b2b00;
  background: #f4e3c2;
  font-size: 0.7rem;
  font-weight: 700;
}

.action-error {
  margin: 0 0 1rem;
}

@media (max-width: 600px) {
  .adreces-content {
    padding-top: 2rem;
  }

  .page-heading,
  .address-card {
    align-items: stretch;
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .address-actions {
    justify-content: flex-end;
  }

  .page-error {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
