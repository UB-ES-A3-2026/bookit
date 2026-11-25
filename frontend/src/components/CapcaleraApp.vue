<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import logoImage from "../assets/bookit-logo.jpg";
import { useSessioStore } from "../stores/sessio.js";
import MenuUsuari from "./MenuUsuari.vue";
import NotificacionsCapcalera from "./NotificacionsCapcalera.vue";

// Capçalera comuna de les pàgines amb sessió: la mateixa per a usuaris,
// biblioteques i repartidors. Només canvia l'enllaç principal segons el rol.
const router = useRouter();
const sessio = useSessioStore();

const ENLLACOS_ROL = {
  usuari: { nom: "cerca", text: "Catàleg" },
  biblioteca: { nom: "cataleg", text: "El meu catàleg" },
  repartidor: { nom: "ruta-repartidor", text: "La meva ruta" },
};

const enllacPrincipal = computed(() => ENLLACOS_ROL[sessio.rol] ?? null);

function tancaSessio() {
  sessio.tancarSessio();
  router.push({ name: "home" });
}
</script>

<template>
  <header class="site-header">
    <div class="site-header__inner">
      <RouterLink class="brand" to="/" aria-label="bookit inici">
        <span
          class="brand-mark"
          :style="{ backgroundImage: `url(${logoImage})` }"
          aria-hidden="true"
        ></span>
        <span>bookit.</span>
      </RouterLink>

      <p class="header-quote">
        “La lectura és per a la ment el que l'exercici és per al cos.” — Joseph
        Addison
      </p>

      <nav class="header-actions" aria-label="Compte">
        <RouterLink
          v-if="enllacPrincipal"
          class="catalog-link"
          :to="{ name: enllacPrincipal.nom }"
        >
          {{ enllacPrincipal.text }}
        </RouterLink>
        <NotificacionsCapcalera />
        <MenuUsuari />
        <button type="button" class="logout-button" @click="tancaSessio">
          Tancar sessió
        </button>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: relative;
  /* Per sobre del contingut, perquè s'hi puguin desplegar els menús. */
  z-index: 5;
  padding: 0 1.25rem;
  background: #fffdf9;
  box-sizing: border-box;
}

.site-header__inner {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 1.5rem;
  max-width: 1170px;
  min-height: 62px;
  margin: 0 auto;
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

.brand:focus-visible {
  outline: 3px solid #ffbf47;
  outline-offset: 3px;
}

.brand-mark {
  display: block;
  width: 2rem;
  height: 2rem;
  border-radius: 0.35rem;
  background-position: center 36%;
  background-size: auto 240%;
}

.header-quote {
  margin: 0;
  color: #6b5d52;
  font-family: Georgia, serif;
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
}

.catalog-link {
  color: #241914;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
}

.catalog-link:hover,
.catalog-link:focus-visible {
  color: #980000;
}

@media (max-width: 1100px) {
  .site-header__inner {
    grid-template-columns: auto 1fr;
  }

  .header-quote {
    display: none;
  }
}

@media (max-width: 600px) {
  .site-header {
    padding: 0.6rem 1rem;
  }

  .header-actions {
    flex-wrap: wrap;
    gap: 0.6rem;
  }

  .catalog-link {
    font-size: 0.85rem;
  }
}
</style>
