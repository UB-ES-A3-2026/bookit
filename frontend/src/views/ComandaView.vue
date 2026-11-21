<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { confirmaComanda, obtenirCostosLliurament } from "../services/prestecs.js";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";

const router = useRouter();
const comanda = useComandaStore();
const sessio = useSessioStore();

const tipus = ref("domicili");
const adreca = ref(sessio.usuari?.address ?? "");
const costos = ref({ domicili: "0.00", recollida: "0.00" });
const carregantCostos = ref(true);
const enviant = ref(false);
const error = ref("");

const costActual = computed(() =>
  tipus.value === "recollida" ? costos.value.recollida : costos.value.domicili,
);

async function carregaCostos() {
  carregantCostos.value = true;
  error.value = "";
  try {
    costos.value = await obtenirCostosLliurament();
  } catch {
    error.value = "No s'han pogut carregar els costos d'enviament.";
  } finally {
    carregantCostos.value = false;
  }
}

async function confirma() {
  error.value = "";
  const biblioteques = new Set(
    comanda.llibres
      .map((llibre) => llibre.biblioteca?.id)
      .filter((id) => id !== undefined && id !== null),
  );

  if (biblioteques.size !== 1) {
    error.value = "No s'ha pogut determinar la biblioteca d'aquesta comanda.";
    return;
  }

  if (tipus.value === "domicili" && !adreca.value.trim()) {
    error.value = "Indica l'adreça de lliurament.";
    return;
  }

  enviant.value = true;
  try {
    await confirmaComanda({
      biblioteca: [...biblioteques][0],
      llibres: comanda.llibres.map((llibre) => llibre.id),
      tipus_lliurament: tipus.value,
      adreca_lliurament:
        tipus.value === "domicili" ? adreca.value.trim() : "",
    });
    comanda.buidar();
  } catch (errorPeticio) {
    const dades = errorPeticio.response?.data;
    error.value =
      dades?.adreca_lliurament?.[0] ??
      dades?.tipus_lliurament?.[0] ??
      dades?.llibres?.[0] ??
      "No s'ha pogut confirmar la comanda.";
  } finally {
    enviant.value = false;
  }
}

onMounted(carregaCostos);
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
      <RouterLink class="back-link" to="/">Torna a l'inici</RouterLink>
    </header>

    <section class="comanda-content">
      <p class="eyebrow">Comanda</p>
      <h1>Tipus de lliurament</h1>

      <p v-if="error" class="avis-error" role="alert">{{ error }}</p>

      <fieldset class="opcions">
        <legend>Com vols rebre la comanda?</legend>
        <label>
          <input v-model="tipus" type="radio" value="domicili" />
          <span>
            <strong>Lliurament a domicili</strong>
            <small>
              {{
                carregantCostos
                  ? "Calculant cost..."
                  : `${Number(costos.domicili).toLocaleString("ca", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })} €`
              }}
            </small>
          </span>
        </label>
        <label>
          <input v-model="tipus" type="radio" value="recollida" />
          <span>
            <strong>Recollida a la biblioteca</strong>
            <small>
              {{
                carregantCostos
                  ? "Calculant cost..."
                  : `${Number(costos.recollida).toLocaleString("ca", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })} €`
              }}
            </small>
          </span>
        </label>
      </fieldset>

      <label v-if="tipus === 'domicili'" class="camp-adreca">
        Adreça de lliurament
        <input v-model="adreca" type="text" autocomplete="street-address" />
      </label>

      <div class="cost-total">
        <span>Cost d'enviament</span>
        <strong>
          {{
            carregantCostos
              ? "Calculant..."
              : `${Number(costActual).toLocaleString("ca", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })} €`
          }}
        </strong>
      </div>

      <button
        type="button"
        class="confirm-button"
        :disabled="comanda.nombreLlibres === 0 || carregantCostos || enviant"
        @click="confirma"
      >
        {{ enviant ? "Confirmant..." : "Confirmar comanda" }}
      </button>
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
.brand,
.back-link {
  color: #271d1a;
  font-weight: 800;
  text-decoration: none;
}
.brand-mark {
  display: inline-block;
  width: 2rem;
  height: 2rem;
  margin-right: 0.55rem;
  border-radius: 0.35rem;
  background-position: center 36%;
  background-size: auto 240%;
  vertical-align: middle;
}
.back-link { color: #a00000; }
.comanda-content {
  max-width: 760px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
}
.eyebrow {
  color: #a00000;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
h1 {
  margin: 0.5rem 0 1.5rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2rem, 4vw, 2.6rem);
}
.avis-error {
  padding: 0.9rem 1rem;
  border: 1px solid #dfc0b0;
  border-radius: 0.55rem;
  color: #870000;
  background: #fff1e8;
  font-weight: 700;
}
.opcions {
  display: grid;
  gap: 0.75rem;
  margin: 0 0 1.25rem;
  padding: 0;
  border: 0;
}
.opcions legend {
  margin-bottom: 0.75rem;
  font-weight: 800;
}
.opcions label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.75rem;
  background: #fffdf8;
  cursor: pointer;
}
.opcions span,
.cost-total {
  display: flex;
  flex: 1;
  justify-content: space-between;
  gap: 1rem;
}
.opcions small { color: #5f544b; }
.camp-adreca {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1.25rem;
  font-weight: 800;
}
.camp-adreca input {
  min-height: 44px;
  padding: 0.65rem 0.75rem;
  border: 1px solid #c9bba6;
  border-radius: 0.55rem;
  font: inherit;
}
.cost-total {
  align-items: center;
  padding: 1rem 0;
  border-top: 1px solid #dfd1bd;
  border-bottom: 1px solid #dfd1bd;
}
.confirm-button {
  margin-top: 1.25rem;
  padding: 0.75rem 1.1rem;
  border: 0;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}
.confirm-button:disabled { opacity: 0.55; cursor: default; }
</style>
