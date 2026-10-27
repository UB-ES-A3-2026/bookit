<script setup>
import { onMounted, onUnmounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import bibliotecaImage from "../assets/biblioteca.jpg";

const router = useRouter();

function tancaCaixa() {
  router.push({ name: "home" });
}

// Només es tanca si el clic comença i acaba al fons. Així, si es selecciona
// text a dins de la caixa i es deixa anar el ratolí a fora, no es tanca.
const fons = ref(null);
let clicComencaAlFons = false;

function recordaOnComencaElClic(event) {
  clicComencaAlFons = event.target === fons.value;
}

function tancaSiEsClicaAlFons(event) {
  if (clicComencaAlFons && event.target === fons.value) {
    tancaCaixa();
  }
}

const formulari = reactive({
  correu: "",
  contrasenya: "",
});

function enviaFormulari() {
  // La connexió amb l'API i la redirecció segons el rol són la US2-T11.
}

// La caixa també es tanca amb la tecla Escape.
function tancaAmbEscape(event) {
  if (event.key === "Escape") {
    tancaCaixa();
  }
}

onMounted(() => window.addEventListener("keydown", tancaAmbEscape));
onUnmounted(() => window.removeEventListener("keydown", tancaAmbEscape));
</script>

<template>
  <main
    class="login-page"
    :style="{ backgroundImage: `url(${bibliotecaImage})` }"
    @mousedown="recordaOnComencaElClic"
    @click="tancaSiEsClicaAlFons"
  >
    <div ref="fons" class="login-page__overlay"></div>

    <section
      class="login-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-title"
    >
      <header class="login-modal__header">
        <div>
          <p class="login-modal__welcome">Benvingut/da a bookit.</p>
          <h1 id="login-title">Inicia Sessió</h1>
        </div>

        <button
          class="login-modal__close"
          type="button"
          aria-label="Tancar"
          @click="tancaCaixa"
        >
          ×
        </button>
      </header>

      <nav class="login-tabs" aria-label="Autenticació">
        <span
          class="login-tabs__tab login-tabs__tab--active"
          aria-current="page"
        >
          Inicia Sessió
        </span>
        <RouterLink class="login-tabs__tab" to="/registre">
          Registrar-se
        </RouterLink>
      </nav>

      <form class="login-form" novalidate @submit.prevent="enviaFormulari">
        <div class="login-form__field">
          <label for="login-correu">Correu electrònic / Nom d'usuari</label>
          <input
            id="login-correu"
            v-model="formulari.correu"
            name="correu"
            type="text"
            autocomplete="username"
            placeholder="nom@exemple.cat"
          />
        </div>

        <div class="login-form__field">
          <label for="login-contrasenya">Contrasenya</label>
          <input
            id="login-contrasenya"
            v-model="formulari.contrasenya"
            name="contrasenya"
            type="password"
            autocomplete="current-password"
            placeholder="La teva contrasenya"
          />
        </div>

        <button class="login-form__submit" type="submit">
          Iniciar Sessió
          <span aria-hidden="true">→</span>
        </button>

        <p class="login-form__note">
          <span aria-hidden="true">✓</span>
          Accediràs automàticament a l'espai corresponent al teu perfil.
        </p>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  min-height: 100svh;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  box-sizing: border-box;
  background-position: center;
  background-size: cover;
  overflow: hidden;
}

.login-page__overlay {
  position: fixed;
  inset: 0;
  background: rgb(25 26 31 / 58%);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.login-modal {
  position: relative;
  z-index: 1;
  width: min(100%, 360px);
  max-height: calc(100svh - 2rem);
  box-sizing: border-box;
  overflow-y: auto;
  padding: 0.8rem 1.25rem;
  border-radius: 0.7rem;
  color: #4d4541;
  background: #fffdf8;
  box-shadow: 0 1.2rem 3rem rgb(0 0 0 / 30%);
}

.login-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.login-modal__welcome {
  margin: 0 0 0.25rem;
  color: #756d66;
  font-size: 0.58rem;
  font-weight: 700;
}

.login-modal h1 {
  margin: 0;
  color: #442d2a;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.login-modal__close {
  display: grid;
  width: 1.7rem;
  height: 1.7rem;
  flex: 0 0 1.7rem;
  place-items: center;
  padding: 0;
  border: 1px solid #e5dcd0;
  border-radius: 0.45rem;
  color: #8d8177;
  background: transparent;
  cursor: pointer;
  font-size: 1.35rem;
  font-weight: 300;
  line-height: 1;
}

.login-modal__close:hover,
.login-modal__close:focus-visible {
  color: #870000;
  border-color: #870000;
}

.login-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.2rem;
  margin-bottom: 0.55rem;
  padding: 0.2rem;
  border-radius: 0.45rem;
  background: #f3ecdf;
}

.login-tabs__tab {
  display: grid;
  min-height: 2.1rem;
  place-items: center;
  padding: 0.45rem 0.35rem;
  border-radius: 0.35rem;
  color: #837a72;
  font-size: 0.7rem;
  font-weight: 700;
  text-decoration: none;
}

.login-tabs__tab--active {
  color: #a00000;
  background: #fffdf8;
  box-shadow: 0 1px 4px rgb(91 47 22 / 14%);
}

.login-tabs__tab:focus-visible {
  outline: 2px solid #a00000;
  outline-offset: 2px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.login-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.login-form__field label {
  color: #4d4541;
  font-size: 0.62rem;
  font-weight: 700;
}

.login-form__field input {
  box-sizing: border-box;
  width: 100%;
  min-height: 1.9rem;
  padding: 0.3rem 0.55rem;
  border: 1px solid #e1d8cd;
  border-radius: 0.35rem;
  color: #4d4541;
  background: #fff;
  font: inherit;
  font-size: 0.63rem;
}

.login-form__field input::placeholder {
  color: #aea7a0;
}

.login-form__field input:focus {
  outline: 2px solid #a00000;
  outline-offset: 1px;
}

.login-form__submit {
  display: flex;
  min-height: 1.9rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.2rem;
  padding: 0.3rem 1rem;
  border: 0;
  border-radius: 0.35rem;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(91 0 0 / 20%);
  cursor: pointer;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 700;
}

.login-form__submit:hover,
.login-form__submit:focus-visible {
  background: #850000;
}

.login-form__submit:focus-visible {
  outline: 2px solid #a00000;
  outline-offset: 2px;
}

.login-form__submit span {
  font-size: 1rem;
  font-weight: 400;
}

.login-form__note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  margin: 0.1rem 0 0.2rem;
  color: #827a73;
  font-size: 0.52rem;
}

.login-form__note span {
  color: #2f7d4a;
  font-weight: 700;
}

@media (max-width: 420px) {
  .login-page {
    align-items: flex-start;
    padding: 0.6rem;
  }

  .login-modal {
    max-height: calc(100svh - 1.2rem);
    padding: 0.8rem 1.1rem;
  }
}
</style>
