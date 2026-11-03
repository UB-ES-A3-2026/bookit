<script setup>
import axios from "axios";
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import bibliotecaImage from "../assets/biblioteca.jpg";

const route = useRoute();
const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const ENLLAC_INVALID = "L'enllaç de verificació no és vàlid o ha caducat.";
const SENSE_CONNEXIO = "No s'ha pogut verificar el compte. Torna-ho a provar més tard.";
const CAMP_OBLIGATORI = "Aquest camp és obligatori.";

// carregant → formulari → correcte, o error si l'enllaç no és vàlid.
const estat = ref("carregant");
const missatge = ref("");
const correu = ref("");
const enviant = ref(false);

const formulari = reactive({ contrasenya: "", confirmarContrasenya: "" });
const errors = reactive({ contrasenya: "", confirmarContrasenya: "" });

function urlVerificacio() {
  const { uidb64, token } = route.params;
  return `${apiUrl}/api/auth/verify/biblioteca/${encodeURIComponent(uidb64)}/${encodeURIComponent(token)}/`;
}

function mostraError(error) {
  estat.value = "error";
  missatge.value = error.response
    ? (error.response.data?.detail ?? ENLLAC_INVALID)
    : SENSE_CONNEXIO;
}

// Comprova l'enllaç abans de demanar la contrasenya, perquè si ha caducat
// la biblioteca ho sàpiga sense haver d'omplir res.
async function comprovaEnllac() {
  const { uidb64, token } = route.params;

  if (!uidb64 || !token) {
    estat.value = "error";
    missatge.value = ENLLAC_INVALID;
    return;
  }

  try {
    const resposta = await axios.get(urlVerificacio());
    correu.value = resposta.data?.correu ?? "";
    estat.value = "formulari";
  } catch (error) {
    mostraError(error);
  }
}

function netejaError(camp) {
  errors[camp] = "";
}

function validaFormulari() {
  errors.contrasenya = formulari.contrasenya ? "" : CAMP_OBLIGATORI;

  if (!formulari.confirmarContrasenya) {
    errors.confirmarContrasenya = CAMP_OBLIGATORI;
  } else if (formulari.confirmarContrasenya !== formulari.contrasenya) {
    errors.confirmarContrasenya = "Les contrasenyes no coincideixen.";
  } else {
    errors.confirmarContrasenya = "";
  }

  return !errors.contrasenya && !errors.confirmarContrasenya;
}

async function activaCompte() {
  if (!validaFormulari()) {
    return;
  }

  enviant.value = true;
  try {
    const resposta = await axios.post(urlVerificacio(), {
      contrasenya: formulari.contrasenya,
    });
    estat.value = "correcte";
    missatge.value =
      resposta.data?.detail ?? "El compte de biblioteca s'ha verificat correctament.";
  } catch (error) {
    const missatgesContrasenya = error.response?.data?.contrasenya;
    if (error.response?.status === 400 && Array.isArray(missatgesContrasenya)) {
      // El backend ha rebutjat la contrasenya: es pot tornar a provar amb una altra.
      errors.contrasenya = missatgesContrasenya.join(" ");
    } else {
      mostraError(error);
    }
  } finally {
    enviant.value = false;
  }
}

onMounted(comprovaEnllac);
</script>

<template>
  <main
    class="verification-page"
    :style="{ backgroundImage: `url(${bibliotecaImage})` }"
  >
    <div class="verification-page__overlay"></div>

    <section class="verification-modal" aria-labelledby="verification-title">
      <p class="verification-modal__welcome">Verificació de compte</p>
      <h1 id="verification-title">Verificació del compte de biblioteca</h1>

      <p v-if="estat === 'carregant'" class="verification-modal__text" role="status">
        Verificant l'enllaç...
      </p>

      <form
        v-else-if="estat === 'formulari'"
        class="verification-form"
        novalidate
        @submit.prevent="activaCompte"
      >
        <p class="verification-modal__text">
          Tria la contrasenya per entrar a bookit
          <template v-if="correu">amb <strong>{{ correu }}</strong></template>.
          En desar-la, el compte quedarà actiu.
        </p>

        <div class="verification-form__field">
          <label for="contrasenya">Contrasenya</label>
          <input
            id="contrasenya"
            v-model="formulari.contrasenya"
            type="password"
            autocomplete="new-password"
            placeholder="Mínim 8 caràcters"
            :aria-invalid="Boolean(errors.contrasenya)"
            aria-describedby="contrasenya-error"
            @input="netejaError('contrasenya')"
          />
          <p id="contrasenya-error" class="verification-form__error" aria-live="polite">
            {{ errors.contrasenya }}
          </p>
        </div>

        <div class="verification-form__field">
          <label for="confirmar-contrasenya">Confirmar contrasenya</label>
          <input
            id="confirmar-contrasenya"
            v-model="formulari.confirmarContrasenya"
            type="password"
            autocomplete="new-password"
            placeholder="Repeteix la contrasenya"
            :aria-invalid="Boolean(errors.confirmarContrasenya)"
            aria-describedby="confirmar-contrasenya-error"
            @input="netejaError('confirmarContrasenya')"
          />
          <p
            id="confirmar-contrasenya-error"
            class="verification-form__error"
            aria-live="polite"
          >
            {{ errors.confirmarContrasenya }}
          </p>
        </div>

        <button class="verification-modal__button" type="submit" :disabled="enviant">
          Activar el compte <span aria-hidden="true">→</span>
        </button>
      </form>

      <template v-else-if="estat === 'correcte'">
        <p
          class="verification-modal__message verification-modal__message--success"
          role="status"
        >
          {{ missatge }}
        </p>
        <p class="verification-modal__text">
          Ja pots iniciar sessió amb el teu correu i la contrasenya que has triat.
        </p>
        <RouterLink class="verification-modal__button" :to="{ name: 'inici-sessio' }">
          Iniciar sessió <span aria-hidden="true">→</span>
        </RouterLink>
      </template>

      <template v-else>
        <p
          class="verification-modal__message verification-modal__message--error"
          role="alert"
        >
          {{ missatge }}
        </p>
        <p class="verification-modal__text">
          Demana un nou enllaç de verificació si el problema continua.
        </p>
      </template>

      <RouterLink v-if="estat !== 'correcte'" class="verification-modal__link" to="/">
        Tornar a l'inici
      </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.verification-page {
  position: relative;
  display: flex;
  min-height: 100svh;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 1rem;
  box-sizing: border-box;
  background-position: center;
  background-size: cover;
}

.verification-page__overlay {
  position: fixed;
  inset: 0;
  background: rgb(25 26 31 / 58%);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.verification-modal {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(100%, 360px);
  box-sizing: border-box;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.1rem 1.25rem;
  border-radius: 0.7rem;
  color: #4d4541;
  background: #fffdf8;
  box-shadow: 0 1.2rem 3rem rgb(0 0 0 / 30%);
}

.verification-modal__welcome {
  margin: 0;
  color: #756d66;
  font-size: 0.58rem;
  font-weight: 700;
}

.verification-modal h1 {
  margin: 0;
  color: #442d2a;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.verification-modal__text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.45;
}

.verification-modal__message {
  margin: 0;
  padding: 0.7rem;
  border-radius: 0.45rem;
  font-size: 0.7rem;
  line-height: 1.45;
}

.verification-modal__message--success {
  color: #155724;
  background: #d4edda;
}

.verification-modal__message--error {
  color: #721c24;
  background: #f8d7da;
}

.verification-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.verification-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.verification-form__field label {
  color: #442d2a;
  font-size: 0.68rem;
  font-weight: 700;
}

.verification-form__field input {
  min-height: 1.9rem;
  padding: 0.3rem 0.6rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.35rem;
  box-sizing: border-box;
  color: #241914;
  background: #fff;
  font: inherit;
  font-size: 0.75rem;
}

.verification-form__field input:focus {
  outline: 2px solid #a00000;
  outline-offset: 1px;
}

.verification-form__field input[aria-invalid="true"] {
  border-color: #a00000;
}

.verification-form__error {
  min-height: 0.9rem;
  margin: 0;
  color: #870000;
  font-size: 0.62rem;
}

.verification-modal__button {
  display: flex;
  min-height: 1.8rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.2rem;
  padding: 0.3rem 1rem;
  border: none;
  border-radius: 0.35rem;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(91 0 0 / 20%);
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

.verification-modal__button:hover,
.verification-modal__button:focus-visible {
  background: #850000;
}

.verification-modal__button:focus-visible {
  outline: 2px solid #ffbf47;
  outline-offset: 2px;
}

.verification-modal__button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.verification-modal__button span {
  font-size: 1rem;
  font-weight: 400;
}

.verification-modal__link {
  align-self: center;
  color: #a00000;
  font-size: 0.68rem;
  font-weight: 700;
}

@media (max-width: 500px) {
  .verification-modal {
    padding: 1.1rem;
  }
}
</style>
