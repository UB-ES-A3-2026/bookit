<script setup>
import axios from "axios";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

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
  <main class="verification-page">
    <section class="verification-card" aria-labelledby="verification-title">
      <p class="verification-card__brand">bookit.</p>
      <h1 id="verification-title">Verificació del compte de biblioteca</h1>

      <p v-if="estat === 'carregant'" role="status">
        Verificant l'enllaç...
      </p>

      <template v-else-if="estat === 'correcte'">
        <p
          class="verification-card__message verification-card__message--success"
          role="status"
        >
          {{ missatge }}
        </p>
        <p>Ja pots iniciar sessió amb el teu compte de biblioteca.</p>
      </template>

      <template v-else>
        <p
          class="verification-card__message verification-card__message--error"
          role="alert"
        >
          {{ missatge }}
        </p>
        <p>Demana un nou enllaç de verificació si el problema continua.</p>
      </template>

      <RouterLink class="verification-card__link" to="/">
        Tornar a l'inici
      </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.verification-page {
  display: grid;
  min-height: 100svh;
  padding: 1.5rem;
  place-items: center;
  box-sizing: border-box;
  color: #241914;
  background: #f9f4eb;
}

.verification-card {
  width: min(100%, 34rem);
  padding: 2.5rem;
  border: 1px solid #dfd1bd;
  border-radius: 1rem;
  background: #fffdf9;
  box-shadow: 0 1rem 2rem rgb(72 0 0 / 10%);
  text-align: center;
}

.verification-card__brand {
  margin-bottom: 1rem;
  color: #980000;
  font-size: 1.5rem;
  font-weight: 800;
}

.verification-card h1 {
  margin: 0 0 1.5rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.7rem, 5vw, 2.3rem);
}

.verification-card__message {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
}

.verification-card__message--success {
  color: #155724;
  background: #d4edda;
}

.verification-card__message--error {
  color: #721c24;
  background: #f8d7da;
}

.verification-card__link {
  display: inline-block;
  margin-top: 1.5rem;
  padding: 0.7rem 1.2rem;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font-weight: 700;
  text-decoration: none;
}

.verification-card__link:focus-visible {
  outline: 3px solid #ffbf47;
  outline-offset: 3px;
}

@media (max-width: 500px) {
  .verification-card {
    padding: 1.5rem;
  }
}
</style>
