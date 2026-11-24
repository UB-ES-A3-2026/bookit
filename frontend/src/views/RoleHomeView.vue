<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const titol = computed(() =>
  route.name === "espai-repartidor" ? "Espai de repartidor" : "Catàleg",
);
</script>

<template>
  <main class="role-page">
    <section class="role-card" aria-labelledby="role-title">
      <h1 id="role-title">{{ titol }}</h1>
      <p>Has iniciat sessió correctament.</p>
      <RouterLink to="/">Tornar a l'inici</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.role-page {
  display: grid;
  min-height: 100svh;
  padding: 1.5rem;
  place-items: center;
  box-sizing: border-box;
  color: #241914;
  background: #f9f4eb;
}

.role-card {
  width: min(100%, 34rem);
  padding: 2rem;
  border: 1px solid #dfd1bd;
  border-radius: 1rem;
  background: #fffdf9;
  box-shadow: 0 1rem 2rem rgb(72 0 0 / 10%);
  text-align: center;
}

.role-card h1 {
  margin-top: 0;
  font-family: Georgia, "Times New Roman", serif;
}

.role-card a {
  color: #980000;
  font-weight: 700;
}
</style>
