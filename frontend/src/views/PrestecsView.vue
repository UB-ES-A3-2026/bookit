<script setup>
import { onMounted, ref } from "vue";
import LayoutCompte from "../components/LayoutCompte.vue";
import { llistaPrestecs } from "../services/prestecs.js";


const prestecs = ref([]);
const carregant = ref(true);
const error = ref("");

function formatData(data) {
  const [any, mes, dia] = data.split("-");
  return `${dia}/${mes}/${any}`;
}

async function carregaPrestecs() {
  carregant.value = true;
  error.value = "";
  try {
    prestecs.value = await llistaPrestecs();
  } catch {
    error.value = "No s'han pogut carregar els llibres en préstec.";
  } finally {
    carregant.value = false;
  }
}

onMounted(carregaPrestecs);
</script>

<template>
  <LayoutCompte
    titol="Els meus préstecs"
    apartat="Préstecs"
    descripcio="Consulta els llibres que tens i fins quan els pots tenir."
  >
    <section class="prestecs-content">
      <p v-if="carregant" class="estat" role="status">
        Carregant els préstecs...
      </p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaPrestecs">
          Tornar-ho a provar
        </button>
      </div>

      <p v-else-if="prestecs.length === 0" class="estat">
        No tens cap llibre en préstec
      </p>

      <ul v-else class="llista-prestecs" aria-label="Llibres en préstec">
        <li
          v-for="prestec in prestecs"
          :key="prestec.id"
          class="prestec"
          :class="{ 'prestec-superat': prestec.termini_superat }"
        >
          <img
            v-if="prestec.llibre.portada"
            class="portada"
            :src="prestec.llibre.portada"
            :alt="`Portada de ${prestec.llibre.titol}`"
          />
          <div v-else class="portada portada-buida" aria-hidden="true">
            {{ prestec.llibre.titol.charAt(0) }}
          </div>

          <div class="dades-prestec">
            <h2>{{ prestec.llibre.titol }}</h2>
            <p class="autor">{{ prestec.llibre.autor }}</p>
            <p class="biblioteca">{{ prestec.biblioteca.nom }}</p>
            <dl>
              <div>
                <dt>Prestat el</dt>
                <dd>{{ formatData(prestec.data_inici) }}</dd>
              </div>
              <div>
                <dt>Data límit</dt>
                <dd>{{ formatData(prestec.data_limit) }}</dd>
              </div>
            </dl>
            <p v-if="prestec.termini_superat" class="avis-superat" role="alert">
              Termini de devolució superat
            </p>
          </div>

          <button type="button" class="return-button" disabled>
            Programar la devolució
          </button>
        </li>
      </ul>
    </section>
  </LayoutCompte>
</template>

<style scoped>
.secondary-button,
.return-button {
  padding: 0.65rem 1.1rem;
  border-radius: 0.55rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.return-button:not(:disabled) {
  border: 0;
  color: #fff;
  background: #980000;
}

.return-button:disabled {
  border: 1px solid #cfc3b3;
  color: #84786c;
  background: #ece5da;
  cursor: default;
}

.prestecs-content {
  min-width: 0;
}

.estat {
  padding: 1.5rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.estat-error {
  color: #870000;
}

.estat-error p {
  margin: 0 0 1rem;
}

.secondary-button {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.llista-prestecs {
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.prestec {
  display: grid;
  grid-template-columns: 100px 1fr auto;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.9rem;
  background: #fffdf8;
}

.prestec-superat {
  border-color: #b73535;
  background: #fff7f3;
}

.portada {
  width: 100px;
  aspect-ratio: 2 / 3;
  border-radius: 0.4rem;
  object-fit: cover;
}

.portada-buida {
  display: grid;
  place-items: center;
  color: #fffdf8;
  background: #980000;
  font-family: Georgia, serif;
  font-size: 2rem;
  font-weight: 700;
}

.dades-prestec h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.2rem;
}

.autor,
.biblioteca {
  margin: 0.35rem 0 0;
  color: #4d4541;
}

dl {
  display: flex;
  gap: 2rem;
  margin: 0.8rem 0 0;
}

dl div {
  display: grid;
  gap: 0.15rem;
}

dt {
  color: #7a6d62;
  font-size: 0.75rem;
  font-weight: 700;
}

dd {
  margin: 0;
  font-weight: 700;
}

.avis-superat {
  margin: 0.75rem 0 0;
  color: #870000;
  font-weight: 800;
}

@media (max-width: 650px) {
  .prestec {
    grid-template-columns: 75px 1fr;
  }

  .portada {
    width: 75px;
  }

  .return-button {
    grid-column: 1 / -1;
  }

  dl {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
