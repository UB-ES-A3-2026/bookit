<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import LayoutCompte from "../components/LayoutCompte.vue";
import { cancellaComanda, llistaMevesComandes } from "../services/comandesUsuari.js";
import { formataDia, textEstat, textLliurament } from "../utils/comandes.js";

const router = useRouter();

const comandes = ref([]);
const carregant = ref(true);
const error = ref("");
const errorsCancel = ref({});
const cancelant = ref({});

const CONFIRMACIO_CANCELACIO = "Segur que vols cancel·lar aquesta comanda?";
const ERROR_COMANDA_SORTIDA = "Aquesta comanda ja ha sortit i no es pot cancel·lar";

async function carregaComandes() {
  carregant.value = true;
  error.value = "";

  try {
    comandes.value = await llistaMevesComandes();
  } catch (errorPeticio) {
    // Només els usuaris actius tenen comandes pròpies.
    if (errorPeticio.response?.status === 403) {
      router.push({ name: "home" });
      return;
    }
    error.value = "No s'han pogut carregar les teves comandes. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

async function gestionaCancelacio(comanda) {
  errorsCancel.value = { ...errorsCancel.value, [comanda.id]: "" };

  if (comanda.estat === "en_cami" || comanda.estat === "lliurada") {
    errorsCancel.value = { ...errorsCancel.value, [comanda.id]: ERROR_COMANDA_SORTIDA };
    return;
  }

  if (comanda.estat !== "rebuda" && comanda.estat !== "preparada") {
    errorsCancel.value = {
      ...errorsCancel.value,
      [comanda.id]: "No es pot cancel·lar aquesta comanda.",
    };
    return;
  }

  if (!window.confirm(CONFIRMACIO_CANCELACIO)) {
    return;
  }

  cancelant.value = { ...cancelant.value, [comanda.id]: true };
  try {
    const comandaActualitzada = await cancellaComanda(comanda.id);
    comandes.value = comandes.value.map((actual) =>
      actual.id === comanda.id ? comandaActualitzada : actual,
    );
  } catch (errorPeticio) {
    const missatge = errorPeticio.response?.data?.detail;
    errorsCancel.value = {
      ...errorsCancel.value,
      [comanda.id]:
        typeof missatge === "string"
          ? missatge
          : "No s'ha pogut cancel·lar la comanda. Torna-ho a provar.",
    };
  } finally {
    cancelant.value = { ...cancelant.value, [comanda.id]: false };
  }
}

onMounted(carregaComandes);
</script>

<template>
  <LayoutCompte
    titol="Les meves comandes"
    apartat="Comandes"
    descripcio="Consulta en quin estat és cada comanda i quan t'arribarà."
  >
    <section class="comandes-content">
      <p v-if="carregant" class="estat" role="status">Carregant les comandes...</p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaComandes">
          Tornar-ho a provar
        </button>
      </div>

      <p v-else-if="comandes.length === 0" class="estat">
        Encara no has fet cap comanda.
      </p>

      <ul v-else class="llista-comandes" aria-label="Les meves comandes">
        <li v-for="comanda in comandes" :key="comanda.id" class="comanda">
          <div class="comanda-capcalera">
            <h2>Comanda {{ comanda.id }}</h2>
            <span class="etiqueta" :class="`etiqueta-${comanda.estat}`">
              {{ textEstat(comanda.estat) }}
            </span>
          </div>

          <dl class="dades-comanda">
            <div>
              <dt>Biblioteca</dt>
              <dd>{{ comanda.biblioteca.nom }}</dd>
            </div>
            <div>
              <dt>Demanada el</dt>
              <dd>{{ formataDia(comanda.creada) }}</dd>
            </div>
            <div v-if="comanda.estat !== 'cancellada'">
              <dt>{{ comanda.estat === "lliurada" ? "Data de lliurament" : "Lliurament previst" }}</dt>
              <dd class="data-lliurament">
                {{ textLliurament(comanda) }}
              </dd>
            </div>
          </dl>

          <ul class="llibres" :aria-label="`Llibres de la comanda ${comanda.id}`">
            <li v-for="llibre in comanda.llibres" :key="llibre.id">
              <span class="titol">{{ llibre.titol }}</span>
              <span class="autor"> · {{ llibre.autor }}</span>
            </li>
          </ul>

          <div v-if="comanda.estat !== 'cancellada'" class="accions-comanda">
            <button
              type="button"
              class="secondary-button cancel-button"
              :disabled="cancelant[comanda.id]"
              @click="gestionaCancelacio(comanda)"
            >
              {{ cancelant[comanda.id] ? "Cancel·lant..." : "Cancel·lar comanda" }}
            </button>
            <p v-if="errorsCancel[comanda.id]" class="error-cancellacio" role="alert">
              {{ errorsCancel[comanda.id] }}
            </p>
          </div>
        </li>
      </ul>
    </section>
  </LayoutCompte>
</template>

<style scoped>
.comandes-content {
  min-width: 0;
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

.secondary-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.accions-comanda {
  margin-top: 1rem;
}

.error-cancellacio {
  margin: 0.75rem 0 0;
  color: #870000;
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
</style>
