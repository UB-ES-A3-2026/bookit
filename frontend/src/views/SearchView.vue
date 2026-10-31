<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

// El text cercat arriba a l'adreça des del cercador de la pàgina d'inici.
const textCercat = computed(() => route.query.q ?? "");
</script>

<template>
  <!-- La llista de resultats amb les dades de l'API és la US4-T8. -->
  <main class="search-page">
    <h1>Resultats de la cerca</h1>
    <p v-if="textCercat">Has cercat «{{ textCercat }}».</p>
    <RouterLink to="/">Torna a l'inici</RouterLink>
  </main>
</template>

<style scoped>
.search-page {
  min-height: 100svh;
  padding: 3rem max(1.25rem, calc((100% - 1170px) / 2));
  box-sizing: border-box;
  color: #241914;
  background: #f9f4eb;
}

.search-page h1 {
  margin: 0 0 1rem;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 2rem;
}

.search-page a {
  color: #a00000;
  font-weight: 700;
}
</style>
