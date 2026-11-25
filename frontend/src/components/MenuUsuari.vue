<script setup>
import { computed, onMounted, onUnmounted, ref, useId } from "vue";
import { useComandaStore } from "../stores/comanda.js";
import { useSessioStore } from "../stores/sessio.js";

const sessio = useSessioStore();
const comanda = useComandaStore();

const idMenu = useId();
const arrel = ref(null);
const boto = ref(null);
const obert = ref(false);

const nomUsuari = computed(
  () => sessio.usuari?.nom ?? sessio.usuari?.correu ?? "Usuari",
);

const inicialsUsuari = computed(() =>
  nomUsuari.value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toLocaleUpperCase())
    .join(""),
);

const ETIQUETES_ROL = {
  usuari: "Usuari",
  biblioteca: "Biblioteca",
  repartidor: "Repartidor",
};

const etiquetaRol = computed(() => ETIQUETES_ROL[sessio.rol] ?? "Compte");

// Cada rol veu només les seccions del seu espai.
const enllacos = computed(() => {
  if (sessio.rol === "usuari") {
    return [
      { nom: "meves-comandes", text: "Les meves comandes" },
      { nom: "comanda", text: "La meva cistella", comptador: comanda.nombreLlibres },
      { nom: "prestecs", text: "Els meus préstecs" },
      { nom: "adreces", text: "Les meves adreces" },
    ];
  }
  if (sessio.rol === "biblioteca") {
    return [
      { nom: "cataleg", text: "El meu catàleg" },
      { nom: "cataleg-afegir", text: "Afegir un llibre" },
      { nom: "comandes-biblioteca", text: "Comandes pendents" },
    ];
  }
  if (sessio.rol === "repartidor") {
    return [
      { nom: "espai-repartidor", text: "Espai del repartidor" },
      { nom: "ruta-repartidor", text: "La meva ruta d'avui" },
      { nom: "franges-repartidor", text: "Franges de disponibilitat" },
    ];
  }
  return [];
});

function commuta() {
  obert.value = !obert.value;
}

function tanca() {
  obert.value = false;
  boto.value?.focus();
}

function tancaSiEsClicaFora(event) {
  if (obert.value && !event.composedPath().includes(arrel.value)) {
    obert.value = false;
  }
}

onMounted(() => document.addEventListener("click", tancaSiEsClicaFora));
onUnmounted(() => document.removeEventListener("click", tancaSiEsClicaFora));
</script>

<template>
  <div ref="arrel" class="menu-usuari" @keydown.esc="tanca">
    <button
      ref="boto"
      class="menu-usuari__boto"
      type="button"
      aria-haspopup="true"
      :aria-expanded="obert ? 'true' : 'false'"
      :aria-controls="idMenu"
      @click="commuta"
    >
      <span class="menu-usuari__avatar" aria-hidden="true">{{ inicialsUsuari }}</span>
      <span class="menu-usuari__identitat">
        <strong>{{ nomUsuari }}</strong>
        <small>{{ etiquetaRol }}</small>
      </span>
      <svg
        class="menu-usuari__fletxa"
        :class="{ 'menu-usuari__fletxa--oberta': obert }"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="m6 9 6 6 6-6" />
      </svg>
    </button>

    <nav
      v-if="obert"
      :id="idMenu"
      class="menu-usuari__panell"
      aria-label="El meu compte"
    >
      <ul>
        <li v-for="enllac in enllacos" :key="enllac.nom">
          <RouterLink
            class="menu-usuari__enllac"
            :to="{ name: enllac.nom }"
            @click="obert = false"
          >
            <span>{{ enllac.text }}</span>
            <span
              v-if="enllac.comptador"
              class="menu-usuari__comptador"
              :aria-label="`${enllac.comptador} llibres`"
            >
              {{ enllac.comptador }}
            </span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
.menu-usuari {
  position: relative;
  flex-shrink: 0;
}

.menu-usuari__boto {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.3rem 0.75rem 0.3rem 0.3rem;
  border: 1px solid #e4d8cc;
  border-radius: 999px;
  color: #241914;
  background: #fffdf9;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.menu-usuari__boto:hover,
.menu-usuari__boto[aria-expanded="true"] {
  border-color: #c9b6a4;
  box-shadow: 0 0.2rem 0.6rem rgb(60 30 10 / 10%);
}

.menu-usuari__boto:focus-visible {
  outline: 3px solid #ffbf47;
  outline-offset: 2px;
}

.menu-usuari__avatar {
  display: grid;
  place-items: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  color: #fff;
  background: #980000;
  font-size: 0.8rem;
  font-weight: 800;
}

.menu-usuari__identitat {
  display: grid;
  line-height: 1.15;
}

.menu-usuari__identitat strong {
  max-width: 10rem;
  overflow: hidden;
  font-size: 0.85rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-usuari__identitat small {
  color: #8a7a6d;
  font-size: 0.7rem;
}

.menu-usuari__fletxa {
  width: 1rem;
  height: 1rem;
  fill: none;
  stroke: #6b5d52;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
  transition: transform 0.2s ease;
}

.menu-usuari__fletxa--oberta {
  transform: rotate(180deg);
}

.menu-usuari__panell {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  z-index: 20;
  min-width: 15rem;
  padding: 0.4rem;
  border: 1px solid #eadfd4;
  border-radius: 0.8rem;
  background: #fffdf9;
  box-shadow: 0 0.8rem 2rem rgb(60 30 10 / 18%);
}

.menu-usuari__panell ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.menu-usuari__enllac {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 0.8rem;
  border-radius: 0.55rem;
  color: #241914;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.menu-usuari__enllac:hover,
.menu-usuari__enllac:focus-visible {
  color: #980000;
  background: #f6ece2;
  outline: none;
}

.menu-usuari__enllac.router-link-exact-active {
  color: #980000;
  background: #f3e6da;
}

.menu-usuari__comptador {
  min-width: 1.4rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  color: #fff;
  background: #980000;
  font-size: 0.75rem;
  font-weight: 800;
  text-align: center;
}

@media (max-width: 700px) {
  .menu-usuari__identitat {
    display: none;
  }
}
</style>
