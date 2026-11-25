<script setup>
import { onMounted, reactive, ref } from "vue";
import LayoutCompte from "../components/LayoutCompte.vue";
import {
  afegeixAdreca,
  editaAdreca,
  llistaAdreces,
  marcaAdrecaPredeterminada,
  suprimeixAdreca,
} from "../services/adreces.js";

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
const ERROR_ZONA_SERVEI =
  "Aquesta adreça està fora de la zona de servei, introdueix una adreça vàlida";
const adreces = ref([]);
const carregant = ref(true);
const error = ref("");
const errorAccio = ref("");
const errorZona = ref("");
const errorGeneral = ref("");
const formulariObert = ref(false);
const editantId = ref(null);
const enviant = ref(false);
const eliminantId = ref(null);
const predeterminantId = ref(null);

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
  errorZona.value = "";
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
      if (camp === "codi_postal" && missatges.includes(ERROR_ZONA_SERVEI)) {
        errorZona.value = ERROR_ZONA_SERVEI;
      }
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

function netejaErrorCamp(camp) {
  errors[camp] = "";
  if (camp === "codi_postal") {
    errorZona.value = "";
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

async function marcaPredeterminada(adreca) {
  if (adreca.predeterminada || predeterminantId.value !== null) {
    return;
  }

  predeterminantId.value = adreca.id;
  errorAccio.value = "";
  try {
    const adrecaActualitzada = await marcaAdrecaPredeterminada(adreca.id);
    adreces.value = adreces.value.map((element) =>
      element.id === adreca.id
        ? adrecaActualitzada
        : { ...element, predeterminada: false },
    );
  } catch (errorPeticio) {
    errorAccio.value =
      errorPeticio.response?.data?.detail ??
      "No s'ha pogut actualitzar l'adreça predeterminada. Torna-ho a provar.";
  } finally {
    predeterminantId.value = null;
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

onMounted(carregaAdreces);
</script>

<template>
  <LayoutCompte
    titol="Les meves adreces de lliurament"
    apartat="Adreces"
    descripcio="Gestiona on vols rebre els teus llibres."
  >
    <template #accions>
      <button
        v-if="!formulariObert"
        type="button"
        class="primary-button add-button"
        @click="iniciaNovaAdreca"
      >
        <span aria-hidden="true">+</span>
        Afegir nova adreça
      </button>
    </template>

    <section class="adreces-content">
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

        <p v-if="errorZona" class="zone-warning" role="alert">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3 2.8 20h18.4L12 3Z" />
            <path d="M12 9v5m0 3h.01" />
          </svg>
          {{ errorZona }}
        </p>
        <p v-if="errorGeneral" class="form-error-general" role="alert">
          {{ errorGeneral }}
        </p>

        <div class="form-grid">
          <div v-for="camp in camps" :key="camp" class="form-field">
            <label :for="`adreca-${camp}`">{{ etiquetesCamps[camp] }}</label>
            <input
              :id="`adreca-${camp}`"
              v-model="formulari[camp]"
              type="text"
              :inputmode="camp === 'codi_postal' ? 'numeric' : undefined"
              :autocomplete="autocompletatCamps[camp]"
              :aria-invalid="Boolean(errors[camp])"
              :aria-describedby="`adreca-${camp}-error`"
              required
              @input="netejaErrorCamp(camp)"
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
            {{
              enviant
                ? "Desant..."
                : editantId === null
                  ? "Afegir adreça"
                  : "Desar canvis"
            }}
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
        <li
          v-for="adreca in adreces"
          :key="adreca.id"
          class="address-card"
          :class="{ 'address-card--default': adreca.predeterminada }"
        >
          <span class="address-icon" aria-hidden="true">
            <svg v-if="adreca.predeterminada" viewBox="0 0 24 24">
              <path d="M3.5 10.5 12 3l8.5 7.5M6 9v11h12V9M9.5 20v-6h5v6" />
            </svg>
            <svg v-else viewBox="0 0 24 24">
              <path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" />
              <circle cx="12" cy="10" r="2.2" />
            </svg>
          </span>

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
              :disabled="enviant || eliminantId !== null || predeterminantId !== null"
              @click="iniciaEdicio(adreca)"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m15 5 4 4M4 20l4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10L4 20Z" />
              </svg>
              Editar
            </button>
            <button
              v-if="!adreca.predeterminada"
              type="button"
              class="secondary-button default-button"
              :aria-label="`Fer predeterminada l'adreça de ${adreca.carrer}`"
              :disabled="enviant || eliminantId !== null || predeterminantId !== null"
              @click="marcaPredeterminada(adreca)"
            >
              <span aria-hidden="true">✓</span>
              {{
                predeterminantId === adreca.id
                  ? "Actualitzant..."
                  : "Fer predeterminada"
              }}
            </button>
            <button
              type="button"
              class="danger-button"
              :aria-label="`Suprimir l'adreça de ${adreca.carrer}`"
              :disabled="enviant || eliminantId !== null || predeterminantId !== null"
              @click="confirmaSupressio(adreca)"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5" />
              </svg>
              {{ eliminantId === adreca.id ? "Eliminant..." : "Eliminar" }}
            </button>
          </div>
        </li>
      </ul>

      <aside class="service-area" aria-label="Zona de servei actual">
        <span class="service-area__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" />
            <circle cx="12" cy="10" r="2.2" />
          </svg>
        </span>
        <div>
          <strong>Zona de servei actual</strong>
          <p>
            Comprovem automàticament que el codi postal de l'adreça sigui dins
            la zona de servei.
          </p>
        </div>
      </aside>
    </section>
  </LayoutCompte>
</template>

<style scoped>
.address-actions,
.form-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

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

.primary-button {
  color: #fff;
  background: #980000;
}

.primary-button:hover,
.primary-button:focus-visible {
  background: #720000;
}

.secondary-button {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.danger-button {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: 1px solid #ead8cf;
  color: #870000;
  background: #fffdf9;
}

.danger-button svg,
.address-actions svg {
  width: 0.9rem;
  height: 0.9rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.primary-button:disabled,
.secondary-button:disabled,
.danger-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.adreces-content {
  min-width: 0;
  max-width: none;
  margin: 0;
  padding: 0 0 2.5rem;
}

.add-button {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.7rem 1.1rem;
  box-shadow: 0 0.2rem 0.35rem rgb(72 0 0 / 20%);
  font-size: 0.82rem;
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
  font-size: 1rem;
  font-weight: 700;
}

.form-heading p {
  margin-top: 0.3rem;
  color: #6b5d52;
  font-size: 0.85rem;
}

.zone-warning {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.75rem 0.85rem;
  margin: 0 0 1rem;
  border: 1px solid #e6b9a7;
  border-radius: 0.5rem;
  color: #7d1713;
  background: #fff0e9;
  font-size: 0.82rem;
  line-height: 1.45;
}

.zone-warning svg {
  width: 1.1rem;
  height: 1.1rem;
  flex: 0 0 1.1rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
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
  gap: 0.65rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.address-card {
  display: grid;
  grid-template-columns: 2.4rem minmax(0, 1fr) auto;
  align-items: start;
  gap: 0.8rem;
  min-height: 5.3rem;
  padding: 0.85rem 1rem;
  border-left: 3px solid transparent;
  border-radius: 0.55rem;
}

.address-card--default {
  border-left-color: #980000;
}

.address-icon,
.service-area__icon {
  display: grid;
  width: 2.4rem;
  height: 2.4rem;
  place-items: center;
  border-radius: 0.5rem;
  color: #980000;
  background: #f4e5c9;
}

.address-icon svg,
.service-area__icon svg {
  width: 1.2rem;
  height: 1.2rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.address-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.address-details address {
  margin-top: 0.3rem;
  color: #4d4541;
  font-size: 0.72rem;
  font-style: normal;
  line-height: 1.55;
}

.default-badge {
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  color: #2f735f;
  background: #e6f4ed;
  font-size: 0.58rem;
  font-weight: 700;
}

.address-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.address-actions .secondary-button,
.address-actions .danger-button {
  min-height: 1.85rem;
  padding: 0.35rem 0.55rem;
  font-size: 0.66rem;
  white-space: nowrap;
}

.default-button {
  color: #55483c;
}

.service-area {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-height: 4.1rem;
  padding: 0.75rem 1rem;
  margin-top: 1rem;
  border-radius: 0.5rem;
  color: #33271f;
  background: #f2e5c8;
}

.service-area__icon {
  flex: 0 0 2.2rem;
  width: 2.2rem;
  height: 2.2rem;
  background: transparent;
}

.service-area strong {
  font-size: 0.72rem;
}

.service-area p {
  margin-top: 0.25rem;
  color: #75695f;
  font-size: 0.63rem;
  line-height: 1.45;
}

.action-error {
  margin: 0 0 1rem;
}

@media (max-width: 900px) {
  .address-card {
    grid-template-columns: 2.2rem minmax(0, 1fr);
  }

  .address-actions {
    grid-column: 2;
    justify-content: flex-start;
  }
}

@media (max-width: 650px) {
  .adreces-content {
    padding-bottom: 1.5rem;
  }

  .add-button {
    padding: 0.6rem 0.85rem;
  }

  .address-card {
    grid-template-columns: 2.2rem minmax(0, 1fr);
    gap: 0.65rem;
    padding: 0.85rem;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .address-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .page-error {
    align-items: flex-start;
    flex-direction: column;
  }

  .address-form {
    padding: 1rem;
  }

  .service-area {
    align-items: flex-start;
  }
}
</style>
