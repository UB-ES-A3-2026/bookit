<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { llistaCataleg } from "../services/cataleg.js";

const router = useRouter();

const llibres = ref([]);
const carregant = ref(true);
const error = ref("");

function textExemplars(quantitat) {
  return quantitat === 1 ? "1 exemplar" : `${quantitat} exemplars`;
}

async function carregaCataleg() {
  carregant.value = true;
  error.value = "";

  try {
    llibres.value = await llistaCataleg();
  } catch (errorPeticio) {
    // Un usuari que no és una biblioteca no pot veure aquesta pàgina.
    if (errorPeticio.response?.status === 403) {
      router.push({ name: "home" });
      return;
    }
    error.value = "No s'ha pogut carregar el catàleg. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

onMounted(carregaCataleg);
</script>

<template>
  <main class="cataleg-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <span class="header-link">Catàleg</span>
    </header>

    <section class="cataleg-content">
      <p class="eyebrow">Espai de biblioteca</p>
      <h1>El meu catàleg</h1>
      <p class="description">
        Aquests són els llibres que la teva biblioteca ofereix a bookit i els
        exemplars que en tens de cadascun.
      </p>

      <p v-if="carregant" class="estat" role="status">Carregant el catàleg...</p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaCataleg">
          Tornar-ho a provar
        </button>
      </div>

      <p v-else-if="llibres.length === 0" class="estat">
        Encara no tens cap llibre al catàleg.
      </p>

      <ul v-else class="llista-llibres" aria-label="Llibres del catàleg">
        <li v-for="llibre in llibres" :key="llibre.id" class="llibre">
          <img
            v-if="llibre.portada"
            class="portada"
            :src="llibre.portada"
            :alt="`Portada de ${llibre.titol}`"
          />
          <span v-else class="portada portada-buida" aria-hidden="true">
            {{ llibre.titol.charAt(0) }}
          </span>

          <div class="dades-llibre">
            <h2>{{ llibre.titol }}</h2>
            <p class="autor">{{ llibre.autor }}</p>
            <p class="isbn">ISBN {{ llibre.isbn }}</p>
          </div>

          <span class="exemplars">{{ textExemplars(llibre.exemplars) }}</span>
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped>
.cataleg-page {
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
}

.cataleg-content {
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

.llista-llibres {
  display: grid;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.llibre {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1rem;
  align-items: center;
  padding: 1rem 1.25rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.portada {
  width: 3rem;
  height: 4.25rem;
  border-radius: 0.3rem;
  object-fit: cover;
}

.portada-buida {
  display: grid;
  place-items: center;
  color: #a00000;
  background: #f5ecdc;
  font-family: Georgia, serif;
  font-size: 1.4rem;
  font-weight: 700;
}

.dades-llibre h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.1rem;
}

.autor,
.isbn {
  margin: 0.2rem 0 0;
  color: #4d4541;
  font-size: 0.9rem;
}

.isbn {
  color: #92867c;
  font-size: 0.8rem;
}

.exemplars {
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  color: #870000;
  background: #f5ecdc;
  font-size: 0.85rem;
  font-weight: 700;
  white-space: nowrap;
}

@media (max-width: 560px) {
  .llibre {
    grid-template-columns: auto 1fr;
  }

  .exemplars {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
