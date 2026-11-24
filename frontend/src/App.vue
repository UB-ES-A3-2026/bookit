<script setup>
import { watch } from "vue";
import { useComandaStore } from "./stores/comanda.js";
import { useSessioStore } from "./stores/sessio.js";

const sessio = useSessioStore();
const comanda = useComandaStore();

// Quan algú inicia o tanca la sessió, la comanda passa a ser la del nou usuari.
watch(
  () => sessio.usuari?.id,
  () => comanda.sincronitza(),
);
</script>

<template>
  <RouterView />
</template>
