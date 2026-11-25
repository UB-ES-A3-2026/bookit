<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";
import { confirmaComanda, obtenirCostosLliurament } from "../services/prestecs.js";

const router = useRouter();
const comanda = useComandaStore();
const sessio = useSessioStore();

const teLlibres = computed(() => comanda.llibres.length > 0);
const nomUsuari = computed(
  () => sessio.usuari?.nom ?? sessio.usuari?.name ?? "Usuari",
);
const correuUsuari = computed(
  () => sessio.usuari?.correu ?? sessio.usuari?.email ?? "",
);
const inicialsUsuari = computed(() =>
  String(nomUsuari.value)
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase(),
);
const missatgeLimit =
  "Has superat el límit de llibres per aquesta comanda, elimina un per continuar";
const missatgeEstoc =
  "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera";
const enviant = ref(false);
const missatgeError = ref("");
const idsSenseEstoc = ref([]);
const apuntatsEspera = ref([]);

// Tipus de lliurament i cost d'enviament (US7).
const tipus = ref("domicili");
const adreca = ref(sessio.usuari?.adreca ?? sessio.usuari?.address ?? "");
const costos = ref({ domicili: "0.00", recollida: "0.00" });
const carregantCostos = ref(true);
const costActual = computed(() =>
  tipus.value === "recollida" ? costos.value.recollida : costos.value.domicili,
);

function formataCost(cost) {
  return `${Number(cost).toLocaleString("ca", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} €`;
}

async function carregaCostos() {
  carregantCostos.value = true;
  try {
    costos.value = await obtenirCostosLliurament();
  } catch {
    missatgeError.value = "No s'han pogut carregar els costos d'enviament.";
  } finally {
    carregantCostos.value = false;
  }
}

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

  if (tipus.value === "domicili" && !adreca.value.trim()) {
    missatgeError.value = "Indica l'adreça de lliurament.";
    return;
  }

  enviant.value = true;
  missatgeError.value = "";
  idsSenseEstoc.value = [];

  try {
    await confirmaComanda({
      biblioteca: [...biblioteques][0],
      llibres: comanda.llibres.map((llibre) => llibre.id),
      tipus_lliurament: tipus.value,
      adreca_lliurament: tipus.value === "domicili" ? adreca.value.trim() : "",
    });
    comanda.buidar();
  } catch (error) {
    const dades = error.response?.data;
    idsSenseEstoc.value = dades?.sense_estoc ?? [];
    missatgeError.value =
      dades?.llibres?.[0] ??
      dades?.biblioteca?.[0] ??
      dades?.tipus_lliurament?.[0] ??
      dades?.adreca_lliurament?.[0] ??
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

onMounted(carregaCostos);
</script>

<template>
  <main class="comanda-page">
    <header class="site-header">
      <div class="header-inner">
        <RouterLink class="brand" to="/" aria-label="bookit inici">
          <span
            class="brand-mark"
            :style="{ backgroundImage: `url(${logoImage})` }"
            aria-hidden="true"
          ></span>
          <span>bookit.</span>
        </RouterLink>

        <p class="header-quote">
          “La lectura és per a la ment el que l'exercici és per al cos.” —
          Joseph Addison
        </p>

        <nav class="header-actions" aria-label="Compte">
          <RouterLink class="catalog-link" to="/cerca">Catàleg</RouterLink>
          <span class="notification-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
              <path d="M10 21h4" />
            </svg>
            <span class="notification-dot"></span>
          </span>
          <span class="header-user">
            <span class="user-avatar" aria-hidden="true">{{ inicialsUsuari }}</span>
            <span class="header-user-copy">
              <strong>{{ nomUsuari }}</strong>
              <small>Usuari</small>
            </span>
          </span>
          <button type="button" class="logout-button" @click="tancaSessio">
            Tancar sessió
          </button>
        </nav>
      </div>
    </header>

    <section class="account-layout">
      <aside class="account-sidebar" aria-label="Navegació del compte">
        <div class="sidebar-profile">
          <span class="sidebar-avatar" aria-hidden="true">{{ inicialsUsuari }}</span>
          <span class="sidebar-user-copy">
            <strong>{{ nomUsuari }}</strong>
            <small>{{ correuUsuari }}</small>
          </span>
        </div>

        <nav class="account-navigation" aria-label="El meu compte">
          <ul>
            <li>
              <span class="account-nav-item" aria-disabled="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="8" r="3.5" />
                  <path d="M5 20v-1a7 7 0 0 1 14 0v1" />
                </svg>
                El meu perfil
              </span>
            </li>
            <li>
              <span class="account-nav-item" aria-disabled="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
                </svg>
                Adreces de lliurament
              </span>
            </li>
            <li>
              <span
                class="account-nav-item account-nav-item--active"
                aria-current="page"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 4h16v16H4zM8 8h8M8 12h8" />
                </svg>
                <span>Les meves comandes</span>
                <span class="nav-count">{{ comanda.nombreLlibres }}</span>
              </span>
            </li>
            <li>
              <span class="account-nav-item" aria-disabled="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M5 4h14v16l-7-4-7 4z" />
                </svg>
                Per llegir
              </span>
            </li>
            <li>
              <span class="account-nav-item" aria-disabled="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 12h14M12 5l7 7-7 7" />
                </svg>
                Per tornar
              </span>
            </li>
          </ul>
        </nav>

        <div class="sidebar-help">
          <strong>Necessites ajuda?</strong>
          <p>Consulta les preguntes freqüents o contacta amb nosaltres.</p>
          <span>Centre d'ajuda <span aria-hidden="true">→</span></span>
        </div>
      </aside>

      <section class="comanda-content" aria-labelledby="page-title">
        <nav class="breadcrumb" aria-label="Ruta de navegació">
          <span>El meu compte</span>
          <span aria-hidden="true">/</span>
          <span>Comandes</span>
        </nav>
        <h1 id="page-title">Les meves comandes</h1>
        <p class="description">
          Prepara els llibres i continua per escollir el lliurament o la recollida.
        </p>

        <div v-if="!teLlibres" class="empty-state">
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

          <section class="order-card" aria-labelledby="order-title">
            <header class="order-card-header">
              <div>
                <p class="order-status">Selecció actual</p>
                <h2 id="order-title">Llibres per demanar</h2>
              </div>
              <span class="book-count">{{ comanda.nombreLlibres }} llibres</span>
            </header>

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
                  <h3>{{ llibre.titol }}</h3>
                  <p class="autor">{{ llibre.autor }}</p>
                  <p
                    v-if="!idsSenseEstoc.includes(llibre.id)"
                    class="availability-status"
                  >
                    Disponible per demanar
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
                  class="remove-button secondary-button"
                  :aria-label="`Treure ${llibre.titol} de la comanda`"
                  @click="eliminaLlibre(llibre.id)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5" />
                  </svg>
                  Eliminar
                </button>
              </li>
            </ul>

            <section class="lliurament" aria-labelledby="lliurament-title">
              <h2 id="lliurament-title">Tipus de lliurament</h2>

              <fieldset class="opcions">
                <legend>Com vols rebre la comanda?</legend>
                <label>
                  <input v-model="tipus" type="radio" value="domicili" />
                  <span>
                    <strong>Lliurament a domicili</strong>
                    <small>
                      {{ carregantCostos ? "Calculant cost..." : formataCost(costos.domicili) }}
                    </small>
                  </span>
                </label>
                <label>
                  <input v-model="tipus" type="radio" value="recollida" />
                  <span>
                    <strong>Recollida a la biblioteca</strong>
                    <small>
                      {{ carregantCostos ? "Calculant cost..." : formataCost(costos.recollida) }}
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
                <strong>{{ carregantCostos ? "Calculant..." : formataCost(costActual) }}</strong>
              </div>
            </section>

            <footer class="resum-comanda">
              <p class="next-step">
                En confirmar, enviarem la comanda a la biblioteca seleccionada.
              </p>
              <button
                type="button"
                class="primary-button confirm-button"
                :disabled="comanda.superaLimit || carregantCostos || enviant"
                @click="confirma"
              >
                {{ enviant ? "Confirmant..." : "Confirmar comanda" }}
                <span aria-hidden="true">→</span>
              </button>
            </footer>
          </section>
        </template>
      </section>
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

.site-header {
  min-height: 56px;
  padding: 0 1.25rem;
}

.header-inner {
  display: grid;
  grid-template-columns: 1fr minmax(12rem, 1.3fr) auto;
  align-items: center;
  width: 100%;
  max-width: 1060px;
  min-height: 56px;
  margin: 0 auto;
  gap: 1.5rem;
}

.header-quote {
  margin: 0;
  color: #76695f;
  font-family: Georgia, serif;
  font-size: 0.62rem;
  text-align: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.catalog-link {
  color: #241914;
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: none;
}

.notification-icon {
  position: relative;
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border: 1px solid #e6d9c8;
  border-radius: 50%;
}

.notification-icon svg {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: #5d5149;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.5;
}

.notification-dot {
  position: absolute;
  top: 0.32rem;
  right: 0.32rem;
  width: 0.32rem;
  height: 0.32rem;
  border-radius: 50%;
  background: #a00000;
}

.header-user {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.2rem 0.55rem 0.2rem 0.2rem;
  border: 1px solid #e6d9c8;
  border-radius: 99px;
}

.user-avatar,
.sidebar-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #a00000;
  font-size: 0.65rem;
  font-weight: 800;
}

.user-avatar {
  width: 1.8rem;
  height: 1.8rem;
}

.header-user-copy,
.sidebar-user-copy {
  display: grid;
  min-width: 0;
}

.header-user-copy strong {
  max-width: 6rem;
  overflow: hidden;
  font-size: 0.63rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-user-copy small {
  color: #817569;
  font-size: 0.55rem;
}

.logout-button {
  padding: 0.3rem 0;
  color: #4d4541;
  background: transparent;
  font-size: 0.62rem;
  font-weight: 500;
}

.logout-button:hover {
  color: #870000;
  background: transparent;
}

.account-layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  align-items: start;
  max-width: 1060px;
  margin: 2.1rem auto 0;
  padding: 0 1rem 2rem;
  gap: 2.1rem;
}

.account-sidebar {
  padding: 0.8rem;
  border: 1px solid #e6d9c8;
  border-radius: 0.65rem;
  background: #fffdf8;
}

.sidebar-profile {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.35rem 0 1rem;
  border-bottom: 1px solid #e6d9c8;
}

.sidebar-avatar {
  width: 2.25rem;
  height: 2.25rem;
  font-size: 0.7rem;
}

.sidebar-user-copy strong {
  overflow: hidden;
  font-size: 0.68rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-user-copy small {
  overflow: hidden;
  color: #817569;
  font-size: 0.58rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-navigation {
  padding: 0.55rem 0;
}

.account-navigation ul {
  display: grid;
  gap: 0.18rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.account-nav-item {
  display: flex;
  align-items: center;
  min-height: 2rem;
  padding: 0 0.55rem;
  border-radius: 0.4rem;
  color: #4d555b;
  font-size: 0.65rem;
  gap: 0.55rem;
}

.account-nav-item svg {
  flex: 0 0 0.9rem;
  width: 0.9rem;
  height: 0.9rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.account-nav-item--active {
  color: #870000;
  background: #f4e9d4;
  font-weight: 700;
}

.nav-count {
  display: grid;
  min-width: 1rem;
  height: 1rem;
  padding: 0 0.15rem;
  margin-left: auto;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #a00000;
  font-size: 0.55rem;
}

.sidebar-help {
  padding: 0.7rem;
  border-radius: 0.45rem;
  background: #f5ecdc;
}

.sidebar-help strong {
  font-size: 0.63rem;
}

.sidebar-help p {
  margin: 0.25rem 0 0.45rem;
  color: #817569;
  font-size: 0.55rem;
  line-height: 1.45;
}

.sidebar-help span {
  color: #870000;
  font-size: 0.58rem;
  font-weight: 700;
}

.comanda-content {
  width: 100%;
  max-width: none;
  min-width: 0;
  padding: 0;
  margin: 0;
}

.breadcrumb {
  display: flex;
  align-items: center;
  margin: 0 0 1rem;
  color: #817569;
  font-size: 0.58rem;
  gap: 0.55rem;
}

.comanda-content h1 {
  margin: 0;
  color: #30211c;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.7rem, 2.5vw, 2rem);
  letter-spacing: -0.02em;
}

.description {
  margin: 0.35rem 0 1.3rem;
  color: #71655c;
  font-size: 0.75rem;
}

.order-card,
.empty-state {
  overflow: hidden;
  border: 1px solid #e2d2bd;
  border-radius: 0.65rem;
  background: #fffdf8;
}

.order-card {
  border-left: 3px solid #a00000;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  gap: 1rem;
}

.empty-state p {
  margin: 0;
  color: #4d4541;
  font-size: 0.75rem;
}

.order-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.05rem 0.85rem;
  border-bottom: 1px solid #e6d9c8;
  gap: 1rem;
}

.order-status {
  margin: 0 0 0.35rem;
  color: #a00000;
  font-size: 0.48rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.order-card-header h2 {
  margin: 0;
  color: #30211c;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1rem;
}

.book-count {
  padding: 0.3rem 0.55rem;
  border-radius: 99px;
  color: #870000;
  background: #f4e9d4;
  font-size: 0.55rem;
  font-weight: 700;
  white-space: nowrap;
}

.llista-comanda {
  display: grid;
  padding: 0 1.05rem;
  margin: 0;
  list-style: none;
}

.llibre {
  display: grid;
  grid-template-columns: 2.5rem minmax(0, 1fr) auto;
  align-items: center;
  padding: 0.6rem 0;
  border: 0;
  border-bottom: 1px solid #e8ddcf;
  border-radius: 0;
  background: transparent;
  gap: 0.8rem;
}

.llibre:last-child {
  border-bottom: 0;
}

.portada {
  width: 2.35rem;
  aspect-ratio: 2 / 3;
  border-radius: 0.18rem;
  object-fit: cover;
}

.portada-per-defecte {
  padding: 0.25rem;
  font-size: 0.48rem;
}

.dades-llibre h3 {
  margin: 0;
  color: #30211c;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 0.74rem;
}

.autor {
  margin: 0.2rem 0 0;
  color: #71655c;
  font-size: 0.58rem;
}

.availability-status {
  margin: 0.25rem 0 0;
  color: #28714b;
  font-size: 0.56rem;
  font-weight: 700;
}

.remove-button {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0;
  border: 0;
  color: #a00000;
  background: transparent;
  font-size: 0.56rem;
  gap: 0.25rem;
}

.remove-button:hover {
  color: #720000;
  background: transparent;
}

.remove-button svg {
  width: 0.8rem;
  height: 0.8rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.avis {
  padding: 0.75rem 0.9rem;
  font-size: 0.7rem;
}

.estoc-error {
  margin-top: 0.45rem;
  padding: 0.55rem;
}

.estoc-error p {
  font-size: 0.62rem;
}

.resum-comanda {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1.05rem;
  border-top: 1px solid #e6d9c8;
  margin: 0;
  gap: 1rem;
}

.next-step {
  margin: 0;
  color: #817569;
  font-size: 0.55rem;
}

.resum-comanda .primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 13rem;
  padding: 0.65rem 0.9rem;
  border-radius: 0.45rem;
  box-shadow: 0 2px 4px rgb(75 0 0 / 16%);
  font-size: 0.72rem;
  gap: 0.5rem;
}

.resum-comanda .primary-button span {
  font-size: 0.95rem;
}

@media (max-width: 760px) {
  .header-inner {
    grid-template-columns: auto 1fr;
    gap: 0.7rem;
  }

  .header-quote {
    display: none;
  }

  .header-actions {
    gap: 0.55rem;
  }

  .header-user-copy,
  .notification-icon {
    display: none;
  }

  .account-layout {
    grid-template-columns: 1fr;
    max-width: 640px;
    margin-top: 1.25rem;
    gap: 1rem;
  }

  .account-sidebar {
    order: 2;
  }

  .comanda-content {
    order: 1;
  }

  .account-navigation ul {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sidebar-help {
    margin-top: 0.5rem;
  }
}

@media (max-width: 480px) {
  .site-header {
    padding: 0 0.75rem;
  }

  .brand {
    font-size: 1rem;
  }

  .brand-mark {
    width: 1.7rem;
    height: 1.7rem;
  }

  .header-actions {
    gap: 0.4rem;
  }

  .logout-button {
    font-size: 0.55rem;
  }

  .account-layout {
    padding: 0 0.75rem 1.5rem;
  }

  .order-card-header,
  .resum-comanda,
  .empty-state {
    align-items: stretch;
    flex-direction: column;
  }

  .resum-comanda .primary-button {
    width: 100%;
  }

  .llibre {
    grid-template-columns: 2.3rem minmax(0, 1fr) auto;
    gap: 0.5rem;
  }

  .remove-button {
    font-size: 0;
  }

  .remove-button svg {
    width: 1rem;
    height: 1rem;
  }
}

/* Tipus de lliurament (US7) */
.lliurament {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #eadfcd;
}
.lliurament h2 {
  margin: 0 0 1rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.3rem;
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
.opcions small {
  color: #5f544b;
}
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
</style>
