<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import CapcaleraApp from "../components/CapcaleraApp.vue";
import MapaParades from "../components/MapaParades.vue";
import { completaParada, fallaParada, llistaRutaAvui } from "../services/ruta.js";

const TIPUS = { recollida: "Recollida", lliurament: "Lliurament" };
const ESTATS_PARADA = {
  completada: "Completada",
  fallida: "Fallida",
  cancellada: "Cancel·lada",
};
const MAX_MOTIU = 500;
const ESTATS = {
  rebuda: "Rebuda",
  preparada: "Preparada",
  en_cami: "En camí",
  lliurada: "Lliurada",
  cancellada: "Cancel·lada",
};

const router = useRouter();

const parades = ref([]);
const carregant = ref(true);
const error = ref("");

// Estat de les accions sobre les parades (US13-T5).
const enviant = ref(null);
const paradaFallant = ref(null);
const motiu = ref("");
const errorMotiu = ref("");
const errorsParada = ref({});
const missatge = ref("");

// L'API ja les envia ordenades; es tornen a ordenar per `ordre` perquè la
// posició que es veu sigui sempre la de la ruta.
const paradesEnOrdre = computed(() =>
  [...parades.value].sort((a, b) => a.ordre - b.ordre || a.id - b.id),
);

function textParades(total) {
  return total === 1 ? "1 parada" : `${total} parades`;
}

// Una recollida es fa a la biblioteca i un lliurament, a l'adreça de l'usuari.
function llocParada(parada) {
  if (parada.tipus === "recollida") {
    return parada.adreca?.biblioteca?.nom ?? "Biblioteca no disponible";
  }
  return parada.adreca?.text || "Adreça no disponible";
}

// Una parada sense `estat_parada` es tracta com a pendent.
function estaPendent(parada) {
  return (parada.estat_parada ?? "pendent") === "pendent";
}

// Un lliurament no es pot completar mentre la recollida de la mateixa comanda
// estigui pendent: la comanda encara no ha sortit de la biblioteca.
function esperaRecollida(parada) {
  return (
    parada.tipus === "lliurament" &&
    parades.value.some(
      (altra) =>
        altra.comanda === parada.comanda && altra.tipus === "recollida" && estaPendent(altra),
    )
  );
}

function obreFallida(parada) {
  paradaFallant.value = parada.id;
  motiu.value = "";
  errorMotiu.value = "";
  missatge.value = "";
  errorsParada.value = { ...errorsParada.value, [parada.id]: "" };
}

function tancaFallida() {
  paradaFallant.value = null;
  motiu.value = "";
  errorMotiu.value = "";
}

function textErrorAccio(errorPeticio) {
  const estat = errorPeticio.response?.status;
  const detall = errorPeticio.response?.data?.detail;
  if (estat === 404) {
    return "Aquesta parada ja no és a la teva ruta.";
  }
  if (estat === 409 && typeof detall === "string") {
    return detall;
  }
  return "No s'ha pogut actualitzar la parada. Torna-ho a provar.";
}

// Després d'una acció es torna a demanar la ruta: completar una parada canvia
// l'estat de la comanda i una parada fallida torna a planificar la comanda.
async function recarregaRuta() {
  try {
    parades.value = await llistaRutaAvui();
  } catch {
    // Es manté la llista actual; el missatge de l'acció ja s'ha mostrat.
  }
}

async function executaAccio(parada, accio, textExit, gestionaError) {
  enviant.value = parada.id;
  missatge.value = "";
  // Una acció nova fa que els errors de les accions anteriors ja no valguin.
  errorsParada.value = {};

  try {
    await accio();
    missatge.value = textExit;
    await recarregaRuta();
    return true;
  } catch (errorPeticio) {
    if (gestionaError?.(errorPeticio)) {
      return false;
    }
    const estat = errorPeticio.response?.status;
    if (estat === 401 || estat === 403) {
      router.push({ name: "home" });
      return false;
    }
    errorsParada.value = { ...errorsParada.value, [parada.id]: textErrorAccio(errorPeticio) };
    if (estat === 404) {
      await recarregaRuta();
    }
    return false;
  } finally {
    enviant.value = null;
  }
}

async function marcaCompletada(parada) {
  if (paradaFallant.value === parada.id) {
    tancaFallida();
  }
  await executaAccio(
    parada,
    () => completaParada(parada.id),
    `Parada ${parada.ordre} marcada com a completada.`,
  );
}

async function confirmaFallida(parada) {
  const text = motiu.value.trim();
  if (!text) {
    errorMotiu.value = "Cal indicar el motiu.";
    return;
  }
  if (text.length > MAX_MOTIU) {
    errorMotiu.value = `El motiu no pot tenir més de ${MAX_MOTIU} caràcters.`;
    return;
  }
  errorMotiu.value = "";

  const fet = await executaAccio(
    parada,
    () => fallaParada(parada.id, text),
    `Parada ${parada.ordre} marcada com a fallida.`,
    (errorPeticio) => {
      // Un motiu rebutjat pel backend es mostra al costat del camp.
      const errorCamp = errorPeticio.response?.data?.motiu;
      if (errorPeticio.response?.status !== 400 || !errorCamp) {
        return false;
      }
      errorMotiu.value = Array.isArray(errorCamp) ? errorCamp[0] : errorCamp;
      return true;
    },
  );
  if (fet) {
    tancaFallida();
  }
}

async function carregaRuta() {
  carregant.value = true;
  error.value = "";

  try {
    parades.value = await llistaRutaAvui();
  } catch (errorPeticio) {
    const estat = errorPeticio.response?.status;
    // Només els repartidors validats tenen ruta.
    if (estat === 403) {
      router.push({ name: "home" });
      return;
    }
    error.value =
      estat === 409
        ? "La teva ruta d'avui té dades inconsistents. Avisa l'equip de bookit."
        : "No s'ha pogut carregar la teva ruta. Torna-ho a provar més tard.";
  } finally {
    carregant.value = false;
  }
}

onMounted(carregaRuta);
</script>

<template>
  <main class="ruta-page">
    <CapcaleraApp />

    <section class="ruta-content">
      <p class="eyebrow">Espai de repartidor</p>
      <h1>La meva ruta d'avui</h1>
      <p class="description">
        Les parades del dia en l'ordre en què les has de fer. Cada comanda es
        recull a la biblioteca abans de lliurar-la.
      </p>

      <p v-if="carregant" class="estat" role="status">Carregant la ruta...</p>

      <div v-else-if="error" class="estat estat-error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="secondary-button" @click="carregaRuta">
          Tornar-ho a provar
        </button>
      </div>

      <p v-else-if="parades.length === 0" class="estat">
        Avui no tens cap parada.
      </p>

      <template v-else>
        <MapaParades :parades="paradesEnOrdre" :lloc-de="llocParada" :tipus="TIPUS" />

        <p class="resum">{{ textParades(parades.length) }}</p>
        <p v-if="missatge" class="missatge-exit" role="status">{{ missatge }}</p>

        <ol class="llista-parades" aria-label="Parades de la ruta d'avui">
          <li
            v-for="parada in paradesEnOrdre"
            :key="parada.id"
            class="parada"
            :class="`parada-${parada.tipus}`"
          >
            <span class="ordre" aria-hidden="true">{{ parada.ordre }}</span>

            <div class="parada-cos">
              <div class="parada-capcalera">
                <h2>
                  <span class="nomes-lector">Parada {{ parada.ordre }}: </span>
                  <span class="tipus">{{ TIPUS[parada.tipus] ?? parada.tipus }}</span>
                </h2>
                <span class="comanda">
                  Comanda {{ parada.comanda }} · {{ ESTATS[parada.estat] ?? parada.estat }}
                </span>
              </div>

              <p class="lloc">{{ llocParada(parada) }}</p>

              <ul class="llibres" :aria-label="`Llibres de la parada ${parada.ordre}`">
                <li v-for="llibre in parada.llibres" :key="llibre.id">
                  <span class="titol">{{ llibre.titol }}</span>
                  <span class="autor"> · {{ llibre.autor }}</span>
                </li>
              </ul>

              <p
                v-if="estaPendent(parada) && esperaRecollida(parada)"
                :id="`espera-recollida-${parada.id}`"
                class="avis-recollida"
              >
                Primer marca la recollida d'aquesta comanda a la biblioteca.
              </p>

              <div v-if="estaPendent(parada)" class="accions-parada">
                <div v-if="paradaFallant !== parada.id" class="botons-parada">
                  <button
                    type="button"
                    class="boto-completada"
                    :disabled="enviant !== null || esperaRecollida(parada)"
                    :aria-label="`Marcar la parada ${parada.ordre} com a completada`"
                    :aria-describedby="esperaRecollida(parada) ? `espera-recollida-${parada.id}` : undefined"
                    @click="marcaCompletada(parada)"
                  >
                    {{ enviant === parada.id ? "Desant..." : "Completada" }}
                  </button>
                  <button
                    type="button"
                    class="boto-fallida"
                    :disabled="enviant !== null"
                    :aria-label="`Marcar la parada ${parada.ordre} com a fallida`"
                    @click="obreFallida(parada)"
                  >
                    Fallida
                  </button>
                </div>

                <form
                  v-else
                  class="form-fallida"
                  novalidate
                  @submit.prevent="confirmaFallida(parada)"
                >
                  <label :for="`motiu-${parada.id}`">Motiu de la parada fallida</label>
                  <textarea
                    :id="`motiu-${parada.id}`"
                    v-model="motiu"
                    rows="3"
                    :maxlength="MAX_MOTIU"
                    required
                    :aria-invalid="errorMotiu ? 'true' : 'false'"
                    :aria-describedby="errorMotiu ? `error-motiu-${parada.id}` : undefined"
                    placeholder="Per exemple: no hi havia ningú al domicili."
                  ></textarea>
                  <p
                    v-if="errorMotiu"
                    :id="`error-motiu-${parada.id}`"
                    class="error-camp"
                    role="alert"
                  >
                    {{ errorMotiu }}
                  </p>
                  <div class="botons-parada">
                    <button type="submit" class="boto-fallida" :disabled="enviant !== null">
                      {{ enviant === parada.id ? "Desant..." : "Confirmar fallida" }}
                    </button>
                    <button
                      type="button"
                      class="secondary-button"
                      :disabled="enviant !== null"
                      @click="tancaFallida"
                    >
                      Cancel·lar
                    </button>
                  </div>
                </form>
              </div>

              <p
                v-else
                class="estat-parada"
                :class="`estat-parada-${parada.estat_parada}`"
              >
                {{ ESTATS_PARADA[parada.estat_parada] ?? parada.estat_parada }}
                <span v-if="parada.motiu" class="motiu"> · {{ parada.motiu }}</span>
              </p>

              <p v-if="errorsParada[parada.id]" class="error-parada" role="alert">
                {{ errorsParada[parada.id] }}
              </p>
            </div>
          </li>
        </ol>
      </template>
    </section>
  </main>
</template>

<style scoped>
.ruta-page {
  min-height: 100svh;
  color: #241914;
  background: #f5ecdc;
}

.ruta-content {
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

.nomes-lector {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.resum {
  margin: 0 0 1rem;
  color: #6b5d52;
  font-weight: 700;
}

.llista-parades {
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.parada {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border: 1px solid #dfd1bd;
  border-left: 0.35rem solid #980000;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.parada-lliurament {
  border-left-color: #1d5a36;
}

.ordre {
  display: grid;
  flex: none;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  place-items: center;
  color: #fff;
  background: #980000;
  font-weight: 800;
}

.parada-lliurament .ordre {
  background: #1d5a36;
}

.parada-cos {
  flex: 1;
  min-width: 0;
}

.parada-capcalera {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.25rem 1rem;
}

.parada h2 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.2rem;
  font-weight: 700;
}

.comanda {
  color: #6b5d52;
  font-size: 0.85rem;
  font-weight: 700;
}

.lloc {
  margin: 0.5rem 0 0.75rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.llibres {
  margin: 0;
  padding: 0.75rem 0 0 1.1rem;
  border-top: 1px solid #efe5d6;
}

.autor {
  color: #4d4541;
}

.missatge-exit {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem;
  border-radius: 0.55rem;
  color: #1d5a36;
  background: #e6f2ea;
  font-weight: 700;
}

.accions-parada {
  margin-top: 1rem;
}

.botons-parada {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.boto-completada,
.boto-fallida {
  padding: 0.6rem 1.1rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.boto-completada {
  background: #1d5a36;
}

.boto-completada:hover,
.boto-completada:focus-visible {
  background: #154429;
}

.boto-fallida {
  background: #980000;
}

.boto-fallida:hover,
.boto-fallida:focus-visible {
  background: #740000;
}

.accions-parada button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-fallida {
  display: grid;
  gap: 0.5rem;
}

.form-fallida label {
  font-weight: 700;
}

.form-fallida textarea {
  padding: 0.6rem 0.75rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.55rem;
  font: inherit;
  resize: vertical;
}

.form-fallida textarea[aria-invalid="true"] {
  border-color: #980000;
}

.avis-recollida {
  margin: 0.75rem 0 0;
  color: #6b4f1d;
  font-weight: 700;
}

.error-camp,
.error-parada {
  margin: 0.5rem 0 0;
  color: #870000;
  font-weight: 700;
}

.estat-parada {
  display: inline-block;
  margin: 1rem 0 0;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  color: #4d4541;
  background: #efe5d6;
  font-size: 0.85rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.estat-parada-completada {
  color: #1d5a36;
  background: #e6f2ea;
}

.estat-parada-fallida {
  color: #870000;
  background: #f8e3e3;
}

.motiu {
  font-weight: 400;
}
</style>
