<script setup>
import bibliotecaImage from "../assets/biblioteca.jpg";

// El formulari de registre passa el nom a l'estat de l'historial. Si s'obre la
// pàgina directament no hi és, i es mostra el missatge sense nom.
const nom = window.history.state?.nom ?? "";
</script>

<template>
  <main
    class="confirmation-page"
    :style="{ backgroundImage: `url(${bibliotecaImage})` }"
  >
    <div class="confirmation-page__overlay"></div>

    <section class="confirmation-modal" aria-labelledby="confirmation-title">
      <p class="confirmation-modal__welcome">Sol·licitud enviada</p>
      <h1 id="confirmation-title">
        {{ nom ? `Gràcies, ${nom}` : "Gràcies per registrar-te" }}
      </h1>

      <p class="confirmation-modal__text">
        Hem rebut la teva sol·licitud per ser repartidor de bookit.
      </p>

      <div class="confirmation-modal__status">
        <span class="confirmation-modal__status-label">Estat del compte</span>
        <strong>Pendent de validació</strong>
      </div>

      <p class="confirmation-modal__text">
        Un administrador revisarà les teves dades. Quan el compte estigui
        validat, podràs iniciar sessió i començar a repartir comandes.
      </p>

      <RouterLink class="confirmation-modal__button" to="/">
        Tornar a l'inici <span aria-hidden="true">→</span>
      </RouterLink>
    </section>
  </main>
</template>

<!-- Mateixos colors i mides que la caixa de registre (RegisterView.vue). -->
<style scoped>
.confirmation-page {
  position: relative;
  display: flex;
  min-height: 100svh;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  box-sizing: border-box;
  background-position: center;
  background-size: cover;
  overflow: hidden;
}

.confirmation-page__overlay {
  position: fixed;
  inset: 0;
  background: rgb(25 26 31 / 58%);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.confirmation-modal {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(100%, 360px);
  box-sizing: border-box;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.1rem 1.25rem;
  border-radius: 0.7rem;
  color: #4d4541;
  background: #fffdf8;
  box-shadow: 0 1.2rem 3rem rgb(0 0 0 / 30%);
}

.confirmation-modal__welcome {
  margin: 0;
  color: #756d66;
  font-size: 0.58rem;
  font-weight: 700;
}

.confirmation-modal h1 {
  margin: 0;
  color: #442d2a;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.confirmation-modal__text {
  margin: 0;
  font-size: 0.7rem;
  line-height: 1.45;
}

.confirmation-modal__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid #dfd1bd;
  border-radius: 0.45rem;
  background: #f9f4eb;
  font-size: 0.7rem;
}

.confirmation-modal__status-label {
  color: #756d66;
  font-weight: 700;
}

.confirmation-modal__status strong {
  color: #a00000;
}

.confirmation-modal__button {
  display: flex;
  min-height: 1.8rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.2rem;
  padding: 0.3rem 1rem;
  border-radius: 0.35rem;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(91 0 0 / 20%);
  font-size: 0.7rem;
  font-weight: 700;
  text-decoration: none;
}

.confirmation-modal__button:hover,
.confirmation-modal__button:focus-visible {
  background: #850000;
}

.confirmation-modal__button:focus-visible {
  outline: 2px solid #a00000;
  outline-offset: 2px;
}

.confirmation-modal__button span {
  font-size: 1rem;
  font-weight: 400;
}
</style>
