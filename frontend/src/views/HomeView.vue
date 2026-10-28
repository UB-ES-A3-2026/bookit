<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import bibliotecaImage from "../assets/biblioteca.jpg";
import logoImage from "../assets/bookit-logo.jpg";

const router = useRouter();

const textCerca = ref("");
const campCerca = ref(null);

// Porta a la pàgina de resultats amb el text cercat a l'adreça (/cerca?q=...).
// Si el camp és buit, no es cerca res i el cursor torna al camp.
function cercaLlibres() {
  const text = textCerca.value.trim();
  if (text === "") {
    campCerca.value.focus();
    return;
  }
  router.push({ name: "cerca", query: { q: text } });
}
</script>

<template>
  <main class="home-page">
    <header class="site-header">
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

      <RouterLink class="register-button" to="/registre">Registra't</RouterLink>
    </header>

    <section
      class="hero-section"
      :style="{ backgroundImage: `url(${bibliotecaImage})` }"
    >
      <div class="hero-content">
        <p class="eyebrow">La literatura, a la porta de casa</p>
        <h1>Històries que arriben<br />fins a tu.</h1>
        <p class="hero-description">
          Descobreix els llibres de les biblioteques de la teva ciutat i rep-los
          a casa de manera fàcil, ràpida i sostenible.
        </p>

        <form class="search-box" role="search" @submit.prevent="cercaLlibres">
          <label class="search-box__label" for="cerca-llibres">
            Cerca llibres per títol, autor o ISBN
          </label>
          <svg
            class="search-box__icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="7" />
            <line x1="16.5" y1="16.5" x2="21" y2="21" />
          </svg>
          <input
            id="cerca-llibres"
            ref="campCerca"
            v-model="textCerca"
            type="search"
            name="q"
            autocomplete="off"
            placeholder="Quin llibre busques?"
          />
          <button type="submit">
            Buscar llibres
            <span aria-hidden="true">→</span>
          </button>
        </form>
      </div>
    </section>

    <footer class="benefits" aria-label="Avantatges de bookit">
      <article class="benefit">
        <span class="benefit-icon" aria-hidden="true">▣</span>
        <div>
          <strong>Més de 20.000 llibres</strong>
          <span>de la xarxa pública</span>
        </div>
      </article>
      <article class="benefit">
        <span class="benefit-icon" aria-hidden="true">◷</span>
        <div>
          <strong>Lliurament en 24–48 h</strong>
          <span>a la teva adreça</span>
        </div>
      </article>
      <article class="benefit">
        <span class="benefit-icon" aria-hidden="true">⌖</span>
        <div>
          <strong>12 biblioteques</strong>
          <span>connectades a prop teu</span>
        </div>
      </article>
    </footer>
  </main>
</template>

<style scoped>
.home-page {
  min-height: 100svh;
  color: #241914;
  background: #f9f4eb;
}

.site-header {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 62px;
  padding: 0 max(1.25rem, calc((100% - 1170px) / 2));
  background: #fffdf9;
  box-sizing: border-box;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  justify-self: start;
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

.header-quote {
  max-width: 30rem;
  color: #92867c;
  font-family: Georgia, serif;
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
}

.register-button {
  justify-self: end;
  padding: 0.65rem 1.2rem;
  border-radius: 0.55rem;
  color: #fff;
  background: #980000;
  box-shadow: 0 0.2rem 0.35rem rgb(72 0 0 / 20%);
  font-weight: 700;
  text-decoration: none;
  transition:
    background-color 0.2s ease,
    transform 0.2s ease;
}

.register-button:hover,
.register-button:focus-visible {
  background: #720000;
  transform: translateY(-1px);
}

.hero-section {
  position: relative;
  display: grid;
  min-height: 618px;
  place-items: start center;
  padding: 4rem 1.5rem 3rem;
  box-sizing: border-box;
  background-position: center;
  background-size: cover;
  background-attachment: fixed;
}

.hero-section::before {
  position: absolute;
  inset: 0;
  content: "";
  background: linear-gradient(
    to bottom,
    rgb(255 253 249 / 88%) 0%,
    rgb(255 253 249 / 42%) 16%,
    rgb(255 253 249 / 18%) 34%,
    rgb(255 253 249 / 18%) 66%,
    rgb(255 253 249 / 42%) 84%,
    rgb(255 253 249 / 90%) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 52rem;
  text-align: center;
  text-shadow: 0 0 1.5rem rgb(255 253 249 / 92%);
}

.eyebrow {
  margin: 0 0 1rem;
  color: #9b2721;
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

.hero-content h1 {
  margin: 0;
  color: #241914;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.8rem, 4vw, 3.25rem);
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
  text-shadow:
    0 0 0.2rem rgb(255 253 249 / 100%),
    0 0 1.25rem rgb(255 253 249 / 95%);
}

.hero-description {
  max-width: 40rem;
  margin: 1rem auto 0;
  padding: 0;
  border-radius: 0;
  color: #211612;
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.35;
  text-shadow: 0 0 0.9rem rgb(255 253 249 / 100%);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  max-width: 46rem;
  margin: 2.5rem auto 0;
  padding: 0.45rem 0.45rem 0.45rem 1.25rem;
  border-radius: 0.6rem;
  background: #fffdf8;
  box-shadow: 0 0.8rem 2rem rgb(36 25 20 / 22%);
  text-shadow: none;
}

/* L'etiqueta no es veu, però els lectors de pantalla la llegeixen. */
.search-box__label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.search-box__icon {
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 1.25rem;
  fill: none;
  stroke: #8e8176;
  stroke-linecap: round;
  stroke-width: 2;
}

.search-box input {
  min-width: 0;
  flex: 1;
  padding: 0.6rem 0;
  border: 0;
  color: #241914;
  background: transparent;
  font: inherit;
  font-size: 0.95rem;
}

.search-box input::placeholder {
  color: #aea7a0;
}

.search-box input:focus {
  outline: none;
}

.search-box:focus-within {
  outline: 2px solid #a00000;
  outline-offset: 2px;
}

.search-box button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.4rem;
  border: 0;
  border-radius: 0.45rem;
  color: #fff;
  background: #980000;
  box-shadow: 0 0.2rem 0.35rem rgb(72 0 0 / 20%);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  white-space: nowrap;
}

.search-box button:hover,
.search-box button:focus-visible {
  background: #720000;
}

.benefits {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  min-height: 88px;
  align-items: center;
  padding: 0 max(1.25rem, calc((100% - 1000px) / 2));
  background: #f5ecdc;
  box-sizing: border-box;
}

.benefit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  padding: 0.35rem 1.5rem;
  color: #40342d;
}

.benefit + .benefit {
  border-left: 1px solid #dfd1bd;
}

.benefit-icon {
  display: grid;
  width: 2.2rem;
  height: 2.2rem;
  flex: 0 0 2.2rem;
  place-items: center;
  border-radius: 0.55rem;
  color: #a00000;
  background: #fff6e5;
  font-size: 1.25rem;
}

.benefit div {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.benefit strong {
  font-size: 0.85rem;
}

.benefit div span {
  color: #8e8176;
  font-size: 0.75rem;
}

@media (max-width: 700px) {
  .site-header {
    grid-template-columns: 1fr auto;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
  }

  .header-quote {
    display: none;
  }

  .hero-section {
    min-height: 31rem;
    padding: 3.5rem 1.25rem 2rem;
  }

  .hero-content h1 {
    font-size: clamp(2.5rem, 12vw, 3.7rem);
  }

  .hero-description {
    font-size: 0.9rem;
  }

  /* En mòbil, el botó passa a sota del camp i ocupa tot l'ample. */
  .search-box {
    flex-wrap: wrap;
    margin-top: 2rem;
    padding: 0.45rem;
  }

  .search-box__icon {
    margin-left: 0.6rem;
  }

  .search-box button {
    flex: 1 0 100%;
    justify-content: center;
  }

  .benefits {
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 1rem;
  }

  .benefit {
    justify-content: flex-start;
    padding: 0.35rem 0;
  }

  .benefit + .benefit {
    border-top: 1px solid #dfd1bd;
    border-left: 0;
    padding-top: 1rem;
  }
}
</style>
