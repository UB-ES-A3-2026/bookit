<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";
import { confirmaComanda } from "../services/prestecs.js";

const router = useRouter();
const comanda = useComandaStore();
const sessio = useSessioStore();

const teLlibres = computed(() => comanda.llibres.length > 0);
const missatgeLimit =
  "Has superat el límit de llibres per aquesta comanda, elimina un per continuar";
const missatgeEstoc =
  "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera";
const enviant = ref(false);
const missatgeError = ref("");
const idsSenseEstoc = ref([]);
const apuntatsEspera = ref([]);

function eliminaLlibre(id) {
  comanda.eliminarLlibre(id);
}

function tornaACercar() {
  router.push({ name: "home" });
}

function tancaSessio() {
  sessio.tancarSessio();
  router.push({ name: "home" });
}

async function confirma() {
  if (comanda.superaLimit) {
    missatgeError.value = missatgeLimit;
    return;
  }

  const biblioteques = new Set(
    comanda.llibres
      .map((llibre) => llibre.biblioteca?.id)
      .filter((id) => id !== undefined && id !== null),
  );

  if (biblioteques.size !== 1) {
    missatgeError.value =
      "No s'ha pogut determinar la biblioteca d'aquesta comanda.";
    return;
  }

  enviant.value = true;
  missatgeError.value = "";
  idsSenseEstoc.value = [];

  try {
    await confirmaComanda({
      biblioteca: [...biblioteques][0],
      llibres: comanda.llibres.map((llibre) => llibre.id),
    });
    comanda.buidar();
  } catch (error) {
    const dades = error.response?.data;
    idsSenseEstoc.value = dades?.sense_estoc ?? [];
    missatgeError.value =
      dades?.llibres?.[0] ??
      dades?.biblioteca?.[0] ??
      "No s'ha pogut confirmar la comanda. Torna-ho a provar.";
  } finally {
    enviant.value = false;
  }
}

function apuntaAEspera(llibre) {
  if (!apuntatsEspera.value.includes(llibre.id)) {
    apuntatsEspera.value.push(llibre.id);
  }
}
</script>

<template>
  <main class="comanda-page">
    <header class="site-header">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <div class="header-accions">
        <span class="header-link">La meva comanda</span>
        <button type="button" class="logout-button" @click="tancaSessio">
          Tancar sessió
        </button>
      </div>
    </header>

    <section class="comanda-content">
      <p class="eyebrow">La meva comanda</p>
      <h1>Els llibres que has triat</h1>
      <p class="description">
        Revisa els llibres abans de confirmar la comanda.
      </p>

      <div v-if="!teLlibres" class="estat">
        <p>Encara no has afegit cap llibre a la comanda.</p>
        <button type="button" class="primary-button" @click="tornaACercar">
          Cercar llibres
        </button>
      </div>

      <template v-else>
        <p v-if="comanda.superaLimit" class="avis avis-limit" role="alert">
          {{ missatgeLimit }}
        </p>
        <p v-if="missatgeError" class="avis avis-error" role="alert">
          {{ missatgeError }}
        </p>

        <ul class="llista-comanda" aria-label="Llibres de la comanda">
          <li v-for="llibre in comanda.llibres" :key="llibre.id" class="llibre">
            <img
              v-if="llibre.portada"
              class="portada"
              :src="llibre.portada"
              :alt="`Portada de ${llibre.titol}`"
            />
            <div v-else class="portada portada-per-defecte" aria-hidden="true">
              <span>{{ llibre.titol }}</span>
            </div>

            <div class="dades-llibre">
              <h2>{{ llibre.titol }}</h2>
              <p class="autor">{{ llibre.autor }}</p>
              <p v-if="llibre.biblioteca" class="biblioteca">
                {{ llibre.biblioteca.nom }}
              </p>
              <div v-if="idsSenseEstoc.includes(llibre.id)" class="estoc-error">
                <p>{{ missatgeEstoc }}</p>
                <button
                  type="button"
                  class="wait-button"
                  :disabled="apuntatsEspera.includes(llibre.id)"
                  @click="apuntaAEspera(llibre)"
                >
                  {{
                    apuntatsEspera.includes(llibre.id)
                      ? "Apuntat a la llista d'espera"
                      : "Apuntar-me a la llista d'espera"
                  }}
                </button>
              </div>
            </div>

            <button
              type="button"
              class="secondary-button"
              :aria-label="`Treure ${llibre.titol} de la comanda`"
              @click="eliminaLlibre(llibre.id)"
            >
              Treure
            </button>
          </li>
        </ul>

        <div class="resum-comanda">
          <strong>{{ comanda.nombreLlibres }} llibres</strong>
          <button
            type="button"
            class="primary-button"
            :disabled="comanda.superaLimit || enviant"
            @click="confirma"
          >
            {{ enviant ? "Confirmant..." : "Confirmar comanda" }}
          </button>
        </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
.comanda-page {
  min-height: 100svh;
  color: #241914;
  background: #f9f4eb;
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

.header-accions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-link {
  color: #a00000;
  font-weight: 700;
}

.logout-button,
.primary-button,
.secondary-button {
  padding: 0.6rem 1.1rem;
  border-radius: 0.55rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.logout-button,
.primary-button {
  border: 0;
  color: #fff;
  background: #980000;
}

.logout-button:hover,
.primary-button:hover:not(:disabled) {
  background: #720000;
}

.secondary-button {
  border: 1px solid #dfd1bd;
  color: #241914;
  background: #fff;
}

.secondary-button:hover {
  background: #f5ecdc;
}

.primary-button:disabled {
  opacity: 0.55;
  cursor: default;
}

.comanda-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
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
  font-size: clamp(2rem, 4vw, 2.6rem);
  letter-spacing: -0.03em;
}

.description {
  margin: 0.75rem 0 2rem;
  color: #4d4541;
}

.estat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
}

.avis {
  margin: 0 0 1rem;
  padding: 0.9rem 1rem;
  border-radius: 0.55rem;
  font-weight: 700;
}

.avis-limit,
.avis-error,
.estoc-error {
  border: 1px solid #dfc0b0;
  color: #870000;
  background: #fff1e8;
}

.estoc-error {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.55rem;
}

.estoc-error p {
  margin: 0 0 0.6rem;
}

.wait-button {
  padding: 0.45rem 0.7rem;
  border: 1px solid #870000;
  border-radius: 0.45rem;
  color: #870000;
  background: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.wait-button:disabled {
  color: #68705f;
  border-color: #9da48f;
  cursor: default;
}

.llista-comanda {
  display: grid;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.llibre {
  display: grid;
  grid-template-columns: 90px 1fr auto;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.9rem;
  background: #fffdf8;
}

.portada {
  width: 90px;
  aspect-ratio: 2 / 3;
  border-radius: 0.4rem;
  object-fit: cover;
}

.portada-per-defecte {
  display: grid;
  place-items: center;
  padding: 0.5rem;
  box-sizing: border-box;
  color: #fffdf8;
  background: linear-gradient(160deg, #a00000, #5c0000);
  font-family: Georgia, serif;
  font-size: 0.8rem;
  font-weight: 700;
  text-align: center;
}

.dades-llibre h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.2rem;
}

.autor,
.biblioteca {
  margin: 0.35rem 0 0;
  color: #4d4541;
}

.biblioteca {
  font-size: 0.9rem;
}

.resum-comanda {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

@media (max-width: 600px) {
  .header-link {
    display: none;
  }

  .estat,
  .resum-comanda {
    align-items: stretch;
    flex-direction: column;
  }

  .llibre {
    grid-template-columns: 70px 1fr;
  }

  .llibre .secondary-button {
    grid-column: 1 / -1;
  }

  .portada {
    width: 70px;
  }
}
</style>
