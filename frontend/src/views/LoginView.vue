<script setup>
import { onMounted, onUnmounted, ref } from "vue";
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
