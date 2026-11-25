<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import CapcaleraApp from "../components/CapcaleraApp.vue";
import {
  llistaComandesBiblioteca,
  lliuraComandaRecollida,
  marcaComandaPreparada,
} from "../services/comandesBiblioteca.js";
import { formataDia, textEstat, textLliurament } from "../utils/comandes.js";

const router = useRouter();

const comandes = ref([]);
const carregant = ref(true);
const error = ref("");
// Comanda que s'està marcant (com a llesta o com a lliurada) i missatges d'error
// de cada comanda.
const marcant = ref(null);
const errorsComanda = ref({});
const missatgeLliurada = ref("");

// Les comandes de recollida preparades les ve a buscar l'usuari a la biblioteca
// (US7-T8). La biblioteca les marca com a lliurades quan les hi dona.
function esperaRecollida(comanda) {
  return comanda.tipus_lliurament === "recollida" && comanda.estat === "preparada";
}

async function carregaComandes({ silenciosa = false } = {}) {
  if (!silenciosa) {
    carregant.value = true;
    error.value = "";
  }

  try {
    comandes.value = await llistaComandesBiblioteca();
  } catch (errorPeticio) {
    // Si falla el refresc després d'una acció, es manté la llista que hi ha.
    if (silenciosa) {
      return;
    }
    // Un compte que no és una biblioteca activa no pot veure aquesta pàgina.
    if (errorPeticio.response?.status === 403) {
      router.push({ name: "home" });
      return;
    }
    error.value = "No s'han pogut carregar les comandes. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

function textErrorMarcar(errorPeticio, accio) {
  const estat = errorPeticio.response?.status;
  if (estat === 409) {
    return (
      errorPeticio.response.data?.detail ??
      `Aquesta comanda ja no es pot marcar com a ${accio}.`
    );
  }
  if (estat === 404) {
    return "Aquesta comanda ja no existeix.";
  }
  return `No s'ha pogut marcar la comanda com a ${accio}. Torna-ho a provar més tard.`;
}

// Fa l'acció sobre la comanda i, si falla, en mostra l'error al costat.
async function marca(comanda, peticio, accio, enAcabar) {
  if (marcant.value !== null) {
    return;
  }
  marcant.value = comanda.id;
  missatgeLliurada.value = "";
  const errors = { ...errorsComanda.value };
  delete errors[comanda.id];
  errorsComanda.value = errors;

  try {
    enAcabar(await peticio(comanda.id));
  } catch (errorPeticio) {
    const estat = errorPeticio.response?.status;
    if (estat === 403) {
      router.push({ name: "home" });
      return;
    }
    errorsComanda.value = {
      ...errorsComanda.value,
      [comanda.id]: textErrorMarcar(errorPeticio, accio),
    };
    // Amb un 409 o un 404 la llista que es veu està desfasada: es torna a demanar.
    if (estat === 409 || estat === 404) {
      await carregaComandes({ silenciosa: true });
    }
  } finally {
    marcant.value = null;
  }
}

function marcaLlesta(comanda) {
  return marca(comanda, marcaComandaPreparada, "llesta", (actualitzada) => {
    // La resposta no porta l'usuari: es conserva el que ja teníem.
    comandes.value = comandes.value.map((actual) =>
      actual.id === comanda.id ? { ...actual, ...actualitzada } : actual,
    );
  });
}

function marcaLliurada(comanda) {
  return marca(comanda, lliuraComandaRecollida, "lliurada", () => {
    // Una comanda lliurada ja no és pendent: surt de la llista.
    comandes.value = comandes.value.filter((actual) => actual.id !== comanda.id);
    missatgeLliurada.value = `La comanda ${comanda.id} s'ha lliurat a l'usuari.`;
  });
}

onMounted(() => carregaComandes());
</script>

<template>
  <main class="comandes-page">
    <CapcaleraApp />

    <section class="comandes-content">
      <p class="eyebrow">Espai de biblioteca</p>
      <h1>Comandes pendents</h1>
      <p class="description">
        Les comandes de la teva biblioteca, de la data de lliurament més propera
        a la més llunyana. Les que encara no tenen data surten al final.
      </p>

      <p v-if="missatgeLliurada" class="missatge-lliurada" role="status">{{ missatgeLliurada }}</p>

      <p v-if="carregant" class="estat" role="status">Carregant les comandes...</p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaComandes()">
          Tornar-ho a provar
        </button>
      </div>

      <p v-else-if="comandes.length === 0" class="estat">
        No tens cap comanda pendent.
      </p>

      <ol v-else class="llista-comandes" aria-label="Comandes pendents">
        <li v-for="comanda in comandes" :key="comanda.id" class="comanda">
          <div class="comanda-capcalera">
            <h2>Comanda {{ comanda.id }}</h2>
            <span class="etiqueta" :class="`etiqueta-${comanda.estat}`">
              {{ textEstat(comanda.estat) }}
            </span>
          </div>
          <p v-if="comanda.estat === 'cancellada'" class="avis-cancellada">
            L'usuari l'ha cancel·lada: no cal preparar-la.
          </p>
          <p v-if="esperaRecollida(comanda)" class="avis-recollida">
            L'usuari la recull a la biblioteca: marca-la com a lliurada quan la vingui a buscar.
          </p>

          <dl class="dades-comanda">
            <div>
              <dt>Lliurament</dt>
              <dd class="data-lliurament">
                {{ textLliurament(comanda) }}
              </dd>
            </div>
            <div>
              <dt>Usuari</dt>
              <dd>{{ comanda.usuari.nom }}</dd>
            </div>
            <div>
              <dt>Demanada el</dt>
              <dd>{{ formataDia(comanda.creada) }}</dd>
            </div>
          </dl>

          <ul class="llibres" :aria-label="`Llibres de la comanda ${comanda.id}`">
            <li v-for="llibre in comanda.llibres" :key="llibre.id">
              <span class="titol">{{ llibre.titol }}</span>
              <span class="autor"> · {{ llibre.autor }}</span>
            </li>
          </ul>

          <div
            v-if="comanda.estat === 'rebuda' || esperaRecollida(comanda) || errorsComanda[comanda.id]"
            class="accions-comanda"
          >
            <button
              v-if="comanda.estat === 'rebuda'"
              type="button"
              class="primary-button"
              :disabled="marcant !== null"
              @click="marcaLlesta(comanda)"
            >
              {{ marcant === comanda.id ? "Marcant..." : "Llesta per a recollida" }}
            </button>
            <button
              v-if="esperaRecollida(comanda)"
              type="button"
              class="primary-button"
              :disabled="marcant !== null"
              @click="marcaLliurada(comanda)"
            >
              {{ marcant === comanda.id ? "Marcant..." : "Lliurada a l'usuari" }}
            </button>
            <p v-if="errorsComanda[comanda.id]" class="error-comanda" role="alert">
              {{ errorsComanda[comanda.id] }}
            </p>
          </div>
        </li>
      </ol>
    </section>
  </main>
</template>

<style scoped>
.comandes-page {
  min-height: 100svh;
  color: #241914;
  background: #f5ecdc;
}

.comandes-content {
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

h1 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.2rem, 4vw, 2.8rem);
  line-height: 1.15;
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

.llista-comandes {
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.comanda {
  padding: 1.25rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.comanda-capcalera {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
}

.comanda h2 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.2rem;
  font-weight: 700;
}

.etiqueta {
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  color: #870000;
  background: #f5ecdc;
  font-size: 0.85rem;
  font-weight: 700;
}

.etiqueta-preparada,
.etiqueta-lliurada {
  color: #1d5a36;
  background: #e3f0e4;
}

.etiqueta-cancellada {
  color: #4d4541;
  background: #e8e4df;
}

.dades-comanda {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 2rem;
  margin: 1rem 0;
}

.dades-comanda dt {
  color: #6b5d52;
  font-size: 0.75rem;
  font-weight: 700;
}

.dades-comanda dd {
  margin: 0;
  font-weight: 700;
}

.llibres {
  margin: 0;
  padding: 0.75rem 0 0 1.1rem;
  border-top: 1px solid #efe5d6;
}

.autor {
  color: #4d4541;
}

.accions-comanda {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #efe5d6;
}

.primary-button {
  padding: 0.6rem 1.1rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.primary-button:hover:not(:disabled),
.primary-button:focus-visible {
  background: #740000;
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.error-comanda {
  margin: 0;
  color: #870000;
  font-weight: 700;
}

.avis-cancellada {
  margin-top: 0.5rem;
  color: #870000;
  font-weight: 700;
}

.avis-recollida {
  margin-top: 0.5rem;
  color: #355f4b;
  font-weight: 700;
}

.missatge-lliurada {
  margin: 0 0 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid #b9d8c6;
  border-radius: 0.55rem;
  color: #2d5a43;
  background: #eef8f2;
  font-weight: 700;
}
</style>
