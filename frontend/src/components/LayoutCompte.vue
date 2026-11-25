<script setup>
import { computed } from "vue";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";
import CapcaleraApp from "./CapcaleraApp.vue";

// Estructura comuna de les pàgines del compte de l'usuari: la capçalera,
// la barra lateral amb les seccions i, al costat, el títol i el contingut de
// cada pàgina. El slot "accions" posa botons al costat del títol.
const props = defineProps({
  titol: { type: String, required: true },
  apartat: { type: String, required: true },
  descripcio: { type: String, default: "" },
});

const sessio = useSessioStore();
const comanda = useComandaStore();

const nomUsuari = computed(
  () => sessio.usuari?.nom ?? sessio.usuari?.correu ?? "Usuari",
);
const correuUsuari = computed(() => sessio.usuari?.correu ?? "");
const inicialsUsuari = computed(() =>
  nomUsuari.value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toLocaleUpperCase())
    .join(""),
);

const seccions = computed(() => [
  {
    nom: "meves-comandes",
    text: "Les meves comandes",
    icona: ["M4 4h16v16H4z", "M8 8h8M8 12h8M8 16h5"],
  },
  {
    nom: "comanda",
    text: "La meva cistella",
    icona: ["M6 7h12l-1 13H7z", "M9 7a3 3 0 0 1 6 0"],
    comptador: comanda.nombreLlibres,
  },
  {
    nom: "prestecs",
    text: "Els meus préstecs",
    icona: ["M5 4h14v16l-7-4-7 4z"],
  },
  {
    nom: "adreces",
    text: "Adreces de lliurament",
    icona: ["M3.5 10.5 12 3l8.5 7.5", "M6 9v11h12V9", "M9.5 20v-6h5v6"],
  },
]);

</script>

<template>
  <div class="compte-pagina">
    <CapcaleraApp />

    <div class="account-layout">
      <aside class="account-sidebar">
        <div class="profile-summary">
          <span class="profile-avatar" aria-hidden="true">{{ inicialsUsuari }}</span>
          <div class="profile-summary__identity">
            <strong>{{ nomUsuari }}</strong>
            <span v-if="correuUsuari">{{ correuUsuari }}</span>
          </div>
        </div>

        <nav class="account-nav" aria-label="Seccions del compte">
          <RouterLink
            v-for="seccio in seccions"
            :key="seccio.nom"
            class="account-nav__link"
            :to="{ name: seccio.nom }"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="tram in seccio.icona" :key="tram" :d="tram" />
            </svg>
            <span class="account-nav__text">{{ seccio.text }}</span>
            <span
              v-if="seccio.comptador"
              class="account-nav__count"
              :aria-label="`${seccio.comptador} llibres`"
            >
              {{ seccio.comptador }}
            </span>
          </RouterLink>
          <RouterLink class="account-nav__link" :to="{ name: 'home' }">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M19 12H6M11 6l-6 6 6 6" />
            </svg>
            <span class="account-nav__text">Tornar a l'inici</span>
          </RouterLink>
        </nav>

        <div class="help-card">
          <strong>Necessites ajuda?</strong>
          <p>Consulta les preguntes freqüents o contacta amb nosaltres.</p>
        </div>
      </aside>

      <main id="contingut-principal" class="account-content">
        <div class="page-heading">
          <div>
            <p class="breadcrumb">
              <span>El meu compte</span>
              <span aria-hidden="true">/</span>
              <span>{{ props.apartat }}</span>
            </p>
            <h1>{{ props.titol }}</h1>
            <p v-if="props.descripcio" class="description">{{ props.descripcio }}</p>
          </div>
          <div v-if="$slots.accions" class="page-heading__accions">
            <slot name="accions" />
          </div>
        </div>

        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.compte-pagina {
  min-height: 100svh;
  color: #241914;
  background: #f5ecdc;
}

.account-layout {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  align-items: start;
  gap: 2.25rem;
  max-width: 1170px;
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
  box-sizing: border-box;
}

.account-sidebar {
  position: sticky;
  top: 1.5rem;
  padding: 0.85rem 0.75rem 0.75rem;
  border: 1px solid #e6d8c5;
  border-radius: 0.75rem;
  background: #fffdf9;
}

.profile-summary {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.35rem 0.25rem 0.85rem;
  border-bottom: 1px solid #e6d8c5;
}

.profile-avatar {
  display: grid;
  flex: 0 0 2.4rem;
  height: 2.4rem;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #980000;
  font-size: 0.78rem;
  font-weight: 800;
}

.profile-summary__identity {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 0.15rem;
}

.profile-summary__identity strong,
.profile-summary__identity span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-summary__identity strong {
  font-size: 0.85rem;
}

.profile-summary__identity span {
  color: #75695f;
  font-size: 0.7rem;
}

.account-nav {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem 0 0.95rem;
}

.account-nav__link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-height: 2.4rem;
  padding: 0.4rem 0.6rem;
  border-radius: 0.5rem;
  color: #49423d;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
}

.account-nav__link svg {
  width: 1.05rem;
  height: 1.05rem;
  flex: 0 0 1.05rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.account-nav__text {
  flex: 1;
}

.account-nav__link:hover,
.account-nav__link:focus-visible {
  color: #870000;
  background: #f8eedd;
  outline: none;
}

.account-nav__link.router-link-exact-active {
  color: #870000;
  background: #f4e5c9;
}

.account-nav__count {
  min-width: 1.3rem;
  padding: 0.05rem 0.4rem;
  border-radius: 999px;
  color: #fff;
  background: #980000;
  font-size: 0.7rem;
  font-weight: 800;
  text-align: center;
}

.help-card {
  padding: 0.8rem 0.75rem;
  border-radius: 0.55rem;
  background: #f5ecdc;
}

.help-card strong {
  font-size: 0.78rem;
}

.help-card p {
  margin: 0.35rem 0 0;
  color: #6b5d52;
  font-size: 0.7rem;
  line-height: 1.5;
}

.account-content {
  min-width: 0;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
}

.breadcrumb {
  display: flex;
  gap: 0.5rem;
  margin: 0 0 0.6rem;
  color: #817569;
  font-size: 0.72rem;
}

.page-heading h1 {
  margin: 0;
  color: #30211c;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.7rem, 2.6vw, 2.1rem);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.description {
  margin: 0.35rem 0 0;
  color: #71655c;
  font-size: 0.9rem;
}

.page-heading__accions {
  flex-shrink: 0;
}

@media (max-width: 800px) {
  .account-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 1rem;
    padding-top: 1rem;
  }

  .account-sidebar {
    position: static;
    min-width: 0;
  }

  /* En pantalles estretes les seccions passen a ser una fila desplaçable. */
  .account-nav {
    display: flex;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .account-nav__link {
    flex: 0 0 auto;
    white-space: nowrap;
  }

  .help-card {
    display: none;
  }
}

@media (max-width: 600px) {
  .page-heading {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
