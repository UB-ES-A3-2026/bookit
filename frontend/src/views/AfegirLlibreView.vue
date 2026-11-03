<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { afegeixLlibre } from "../services/cataleg.js";
import { useSessioStore } from "../stores/sessio.js";
import { esEnllacValid, esIsbnValid } from "../utils/validacions.js";

const router = useRouter();
const sessio = useSessioStore();

// Missatges dels criteris d'acceptació (US17) i del contracte (docs/api-cataleg.md).
const CAMPS_OBLIGATORIS = "Omple tots els camps obligatoris per continuar";
const ISBN_INVALID = "L'ISBN introduït no és vàlid";
const EXEMPLARS_NO_ENTER = "Es requereix un nombre enter vàlid.";
const EXEMPLARS_MINIM = "Aquest valor ha de ser més gran o igual a 1.";
const PORTADA_INVALIDA = "Introduïu una URL vàlida.";

const OBLIGATORIS = ["titol", "autor", "isbn", "exemplars"];

const nomBiblioteca = computed(() => sessio.usuari?.nom ?? "La teva biblioteca");

const formulari = reactive({
  titol: "",
  autor: "",
  isbn: "",
  exemplars: "",
  portada: "",
});

const errors = reactive({
  titol: "",
  autor: "",
  isbn: "",
  exemplars: "",
  portada: "",
});

// Camps obligatoris que s'han deixat buits. El missatge és el mateix per a
// tots, així que es mostra una sola vegada a sobre del formulari.
const campsBuits = ref([]);
const errorGeneral = ref("");
const enviant = ref(false);

// Valor del camp sense espais. El camp d'exemplars és numèric i Vue el desa
// com a nombre, per això es passa a text.
function valor(camp) {
  return String(formulari[camp]).trim();
}

function netejaErrors() {
  Object.keys(errors).forEach((camp) => {
    errors[camp] = "";
  });
  campsBuits.value = [];
  errorGeneral.value = "";
}

function netejaFormulari() {
  Object.keys(formulari).forEach((camp) => {
    formulari[camp] = "";
  });
  netejaErrors();
}

function netejaErrorCamp(camp) {
  errors[camp] = "";
  campsBuits.value = campsBuits.value.filter((buit) => buit !== camp);
  if (campsBuits.value.length === 0 && errorGeneral.value === CAMPS_OBLIGATORIS) {
    errorGeneral.value = "";
  }
}

function teError(camp) {
  return Boolean(errors[camp]) || campsBuits.value.includes(camp);
}

function errorExemplars(text) {
  if (!/^-?[0-9]+$/.test(text)) {
    return EXEMPLARS_NO_ENTER;
  }
  return Number(text) < 1 ? EXEMPLARS_MINIM : "";
}

// Comprova el formulari abans d'enviar-lo. La validació definitiva la fa el
// backend, però així l'usuari veu els errors més habituals sense esperar.
function validaFormulari() {
  campsBuits.value = OBLIGATORIS.filter((camp) => !valor(camp));
  if (campsBuits.value.length > 0) {
    errorGeneral.value = CAMPS_OBLIGATORIS;
  }

  if (valor("isbn") && !esIsbnValid(valor("isbn"))) {
    errors.isbn = ISBN_INVALID;
  }
  if (valor("exemplars")) {
    errors.exemplars = errorExemplars(valor("exemplars"));
  }
  if (valor("portada") && !esEnllacValid(valor("portada"))) {
    errors.portada = PORTADA_INVALIDA;
  }

  return campsBuits.value.length === 0 && Object.values(errors).every((error) => !error);
}

// Posa cada missatge del backend sota el seu camp. El de camps obligatoris va a
// dalt, com quan el detecta el client.
function assignaErrorsBackend(errorsBackend) {
  let errorAssignat = false;

  Object.entries(errorsBackend).forEach(([camp, missatges]) => {
    if (!(camp in errors) || !Array.isArray(missatges)) {
      return;
    }
    if (missatges.includes(CAMPS_OBLIGATORIS)) {
      campsBuits.value.push(camp);
      errorGeneral.value = CAMPS_OBLIGATORIS;
    } else {
      errors[camp] = missatges.join(" ");
    }
    errorAssignat = true;
  });

  if (!errorAssignat) {
    errorGeneral.value =
      "No s'ha pogut afegir el llibre. Revisa les dades i torna-ho a provar.";
  }
}

async function enviaFormulari() {
  netejaErrors();

  if (!validaFormulari()) {
    return;
  }

  enviant.value = true;
  try {
    await afegeixLlibre({
      titol: valor("titol"),
      autor: valor("autor"),
      isbn: valor("isbn"),
      exemplars: Number(valor("exemplars")),
      portada: valor("portada"),
    });
    router.push({ name: "cataleg" });
  } catch (error) {
    const estat = error.response?.status;
    if (estat === 400 && error.response.data) {
      assignaErrorsBackend(error.response.data);
    } else if (estat === 403) {
      // Un usuari que no és una biblioteca no pot afegir llibres.
      router.push({ name: "home" });
    } else {
      errorGeneral.value = "No s'ha pogut afegir el llibre. Torna-ho a provar més tard.";
    }
  } finally {
    enviant.value = false;
  }
}
</script>

<template>
  <main class="afegir-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <RouterLink class="header-link" :to="{ name: 'cataleg' }">Catàleg</RouterLink>
    </header>

    <div class="afegir-content">
      <section class="afegir-intro">
        <p class="eyebrow">Espai de biblioteca</p>
        <h1>Afegir un llibre</h1>
        <p class="description">
          Incorpora un títol nou al catàleg perquè els usuaris el puguin trobar i
          demanar.
        </p>

        <div class="biblioteca-card">
          <span class="biblioteca-card__icona" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <rect x="5" y="6" width="14" height="12" rx="1.5" />
              <path d="M8 9h8M8 15h4" />
            </svg>
          </span>
          <div>
            <strong>{{ nomBiblioteca }}</strong>
            <span>El llibre quedarà associat a aquesta biblioteca.</span>
          </div>
        </div>
      </section>

      <form class="llibre-form" novalidate @submit.prevent="enviaFormulari">
        <div class="llibre-form__capcalera">
          <div>
            <h2>Dades del llibre</h2>
            <p>La portada és opcional; la resta de camps són obligatoris.</p>
          </div>
          <span class="etiqueta">Nou títol</span>
        </div>

        <p v-if="errorGeneral" class="llibre-form__error-general" role="alert">
          {{ errorGeneral }}
        </p>

        <div class="llibre-form__camp">
          <label for="titol">Títol</label>
          <input
            id="titol"
            v-model="formulari.titol"
            type="text"
            placeholder="Títol del llibre"
            :aria-invalid="teError('titol')"
            aria-describedby="titol-error"
            @input="netejaErrorCamp('titol')"
          />
          <p id="titol-error" class="llibre-form__error" aria-live="polite">
            {{ errors.titol }}
          </p>
        </div>

        <div class="llibre-form__camp">
          <label for="autor">Autor o autora</label>
          <input
            id="autor"
            v-model="formulari.autor"
            type="text"
            placeholder="Nom complet"
            :aria-invalid="teError('autor')"
            aria-describedby="autor-error"
            @input="netejaErrorCamp('autor')"
          />
          <p id="autor-error" class="llibre-form__error" aria-live="polite">
            {{ errors.autor }}
          </p>
        </div>

        <div class="llibre-form__fila">
          <div class="llibre-form__camp">
            <label for="isbn">ISBN</label>
            <input
              id="isbn"
              v-model="formulari.isbn"
              type="text"
              inputmode="numeric"
              placeholder="978-84-…"
              :aria-invalid="teError('isbn')"
              aria-describedby="isbn-error"
              @input="netejaErrorCamp('isbn')"
            />
            <p id="isbn-error" class="llibre-form__error" aria-live="polite">
              {{ errors.isbn }}
            </p>
          </div>

          <div class="llibre-form__camp">
            <label for="exemplars">Nombre d'exemplars</label>
            <input
              id="exemplars"
              v-model="formulari.exemplars"
              type="number"
              min="1"
              step="1"
              placeholder="1"
              :aria-invalid="teError('exemplars')"
              aria-describedby="exemplars-error"
              @input="netejaErrorCamp('exemplars')"
            />
            <p id="exemplars-error" class="llibre-form__error" aria-live="polite">
              {{ errors.exemplars }}
            </p>
          </div>
        </div>

        <div class="llibre-form__camp">
          <label for="portada">Enllaç de la portada <span>(opcional)</span></label>
          <input
            id="portada"
            v-model="formulari.portada"
            type="url"
            placeholder="https://…"
            :aria-invalid="teError('portada')"
            aria-describedby="portada-error"
            @input="netejaErrorCamp('portada')"
          />
          <p id="portada-error" class="llibre-form__error" aria-live="polite">
            {{ errors.portada }}
          </p>
        </div>

        <div class="llibre-form__botons">
          <button type="button" class="boto-secundari" @click="netejaFormulari">
            Netejar
          </button>
          <button type="submit" class="boto-principal" :disabled="enviant">
            Afegir al catàleg
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
    </div>
  </main>
</template>

<style scoped>
.afegir-page {
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

.header-link {
  color: #241914;
  font-size: 1.05rem;
  font-weight: 700;
  text-decoration: none;
}

.afegir-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
  gap: 3rem;
  max-width: 1040px;
  margin: 0 auto;
  padding: 3.5rem 1.25rem;
  align-items: start;
}

.eyebrow {
  margin: 1.5rem 0 0.75rem;
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
  font-size: clamp(2.2rem, 4vw, 2.8rem);
  letter-spacing: -0.03em;
}

.description {
  margin: 0.75rem 0 2rem;
  color: #4d4541;
  line-height: 1.6;
}

.biblioteca-card {
  display: flex;
  gap: 0.9rem;
  align-items: center;
  padding: 1rem 1.1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.biblioteca-card__icona {
  display: grid;
  flex: 0 0 2.4rem;
  height: 2.4rem;
  place-items: center;
  border-radius: 0.5rem;
  color: #870000;
  background: #f5ecdc;
}

.biblioteca-card__icona svg {
  width: 1.2rem;
  height: 1.2rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-width: 1.7;
}

.biblioteca-card strong {
  display: block;
  font-size: 0.9rem;
}

.biblioteca-card span {
  color: #4d4541;
  font-size: 0.8rem;
}

.llibre-form {
  padding: 2rem;
  border: 1px solid #dfd1bd;
  border-radius: 1rem;
  background: #fffdf8;
  box-shadow: 0 0.8rem 2rem rgb(72 40 20 / 8%);
}

.llibre-form__capcalera {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.25rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid #dfd1bd;
}

.llibre-form__capcalera h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.5rem;
}

.llibre-form__capcalera p {
  margin: 0.4rem 0 0;
  color: #4d4541;
  font-size: 0.8rem;
}

.etiqueta {
  align-self: start;
  padding: 0.35rem 0.6rem;
  border-radius: 0.4rem;
  color: #870000;
  background: #f5ecdc;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.llibre-form__error-general {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 0.6rem;
  color: #870000;
  background: #fbeaea;
  font-size: 0.9rem;
  font-weight: 700;
}

.llibre-form__fila {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.llibre-form__camp label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
  font-weight: 700;
}

.llibre-form__camp label span {
  color: #92867c;
  font-weight: 400;
}

.llibre-form__camp input {
  width: 100%;
  padding: 0.8rem 0.9rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.55rem;
  box-sizing: border-box;
  color: #241914;
  background: #fff;
  font: inherit;
}

.llibre-form__camp input:focus {
  outline: 2px solid #a00000;
  outline-offset: 1px;
}

.llibre-form__camp input[aria-invalid="true"] {
  border-color: #a00000;
}

.llibre-form__error {
  min-height: 1.1rem;
  margin: 0.3rem 0 0.6rem;
  color: #870000;
  font-size: 0.8rem;
}

.llibre-form__botons {
  display: flex;
  justify-content: flex-end;
  gap: 0.8rem;
  margin-top: 0.5rem;
}

.boto-secundari,
.boto-principal {
  padding: 0.8rem 1.3rem;
  border-radius: 0.55rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.boto-secundari {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.boto-principal {
  border: none;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(72 0 0 / 20%);
}

.boto-principal:hover,
.boto-principal:focus-visible {
  background: #720000;
}

.boto-principal:disabled {
  cursor: wait;
  opacity: 0.7;
}

@media (max-width: 800px) {
  .afegir-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    padding-top: 2rem;
  }

  .eyebrow {
    margin-top: 0;
  }
}

@media (max-width: 480px) {
  .llibre-form {
    padding: 1.25rem;
  }

  .llibre-form__fila {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .llibre-form__botons {
    flex-direction: column-reverse;
  }
}
</style>
