<script setup>
import axios from "axios";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import bibliotecaImage from "../assets/biblioteca.jpg";

const route = useRoute();
const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const estat = ref("carregant");
const missatge = ref("");

async function verificaCompte() {
  const { uidb64, token } = route.params;

  if (!uidb64 || !token) {
    estat.value = "error";
    missatge.value = "L'enllaç de verificació no és vàlid o ha caducat.";
    return;
  }

  try {
    const resposta = await axios.get(
      `${apiUrl}/api/auth/verify/biblioteca/${encodeURIComponent(uidb64)}/${encodeURIComponent(token)}/`,
    );
    estat.value = "correcte";
    missatge.value =
      resposta.data?.detail ??
      "El compte de biblioteca s'ha verificat correctament.";
  } catch (error) {
    estat.value = "error";
    missatge.value = error.response
      ? (error.response.data?.detail ??
        "L'enllaç de verificació no és vàlid o ha caducat.")
      : "No s'ha pogut verificar el compte. Torna-ho a provar més tard.";
  }
}

onMounted(verificaCompte);
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

      <template v-else-if="estat === 'correcte'">
        <p
          class="verification-modal__message verification-modal__message--success"
          role="status"
        >
          {{ missatge }}
        </p>
        <p class="verification-modal__text">
          Ja pots iniciar sessió amb el teu compte de biblioteca.
        </p>
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

      <RouterLink class="verification-modal__button" to="/">
        Tornar a l'inici <span aria-hidden="true">→</span>
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

.verification-modal__button {
  display: flex;
  min-height: 1.8rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.2rem;
  padding: 0.3rem 1rem;
  border-radius: 0.35rem;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(91 0 0 / 20%);
  font-size: 0.7rem;
  font-weight: 700;
  text-decoration: none;
}

.verification-modal__button:hover,
.verification-modal__button:focus-visible {
  background: #850000;
}

.verification-modal__button:focus-visible {
  outline: 2px solid #ffbf47;
  outline-offset: 2px;
}

.verification-modal__button span {
  font-size: 1rem;
  font-weight: 400;
}

@media (max-width: 500px) {
  .verification-modal {
    padding: 1.1rem;
  }
}
</style>
