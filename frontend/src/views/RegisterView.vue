<script setup>
import { useRouter } from "vue-router";
import bibliotecaImage from "../assets/biblioteca.jpg";

const router = useRouter();

function tornaInici() {
  router.push({ name: "home" });
}
</script>

<template>
  <main
    class="register-page"
    :style="{ backgroundImage: `url(${bibliotecaImage})` }"
  >
    <div class="register-page__overlay"></div>

    <section class="register-modal" aria-labelledby="register-title">
      <header class="register-modal__header">
        <div>
          <p class="register-modal__welcome">Benvingut/da a bookit.</p>
          <h1 id="register-title">Crear un compte</h1>
        </div>

        <button
          class="register-modal__close"
          type="button"
          aria-label="Tancar"
          @click="tornaInici"
        >
          ×
        </button>
      </header>

      <nav class="register-tabs" aria-label="Autenticació">
        <button class="register-tabs__tab" type="button">Inicia Sessió</button>
        <button
          class="register-tabs__tab register-tabs__tab--active"
          type="button"
        >
          Registrar-se
        </button>
      </nav>

      <form class="register-form">
        <fieldset class="account-type">
          <legend>Com et vols registrar?</legend>

          <div class="account-type__options">
            <button
              class="account-type__option account-type__option--active"
              type="button"
              aria-pressed="true"
            >
              <span aria-hidden="true">♙</span>
              Lector
            </button>

            <button
              class="account-type__option"
              type="button"
              aria-pressed="false"
            >
              <span aria-hidden="true">→</span>
              Repartidor
            </button>

            <button
              class="account-type__option"
              type="button"
              aria-pressed="false"
            >
              <span aria-hidden="true">▣</span>
              Biblioteca
            </button>
          </div>
        </fieldset>

        <div class="register-form__field">
          <label for="correu">Correu electrònic</label>
          <input
            id="correu"
            name="correu"
            type="email"
            autocomplete="email"
            placeholder="nom@exemple.cat"
            aria-describedby="correu-error"
          />
          <p
            id="correu-error"
            class="register-form__error"
            aria-live="polite"
          ></p>
        </div>

        <div class="register-form__field">
          <label for="nom">Nom complet</label>
          <input
            id="nom"
            name="nom"
            type="text"
            autocomplete="name"
            placeholder="p. ex. Laia Vidal Serra"
            aria-describedby="nom-error"
          />
          <p id="nom-error" class="register-form__error" aria-live="polite"></p>
        </div>

        <div class="register-form__field">
          <label for="adreca">Adreça física</label>
          <input
            id="adreca"
            name="adreca"
            type="text"
            autocomplete="street-address"
            placeholder="Carrer, número, pis i porta"
            aria-describedby="adreca-error"
          />
          <p
            id="adreca-error"
            class="register-form__error"
            aria-live="polite"
          ></p>
        </div>

        <div class="register-form__field">
          <label for="num-carnet">Número de carnet de biblioteca</label>
          <input
            id="num-carnet"
            name="num_carnet"
            type="text"
            inputmode="numeric"
            autocomplete="off"
            placeholder="BIB-00000000"
            aria-describedby="num-carnet-help num-carnet-error"
          />
          <p id="num-carnet-help" class="register-form__help">
            El trobaràs al revers del teu carnet.
          </p>
          <p
            id="num-carnet-error"
            class="register-form__error"
            aria-live="polite"
          ></p>
        </div>

        <div class="register-form__field">
          <label for="contrasenya">Contrasenya</label>
          <input
            id="contrasenya"
            name="contrasenya"
            type="password"
            autocomplete="new-password"
            placeholder="Mínim 8 caràcters"
            aria-describedby="contrasenya-error"
          />
          <p
            id="contrasenya-error"
            class="register-form__error"
            aria-live="polite"
          ></p>
        </div>

        <div class="register-form__field">
          <label for="confirmar-contrasenya">Confirmar contrasenya</label>
          <input
            id="confirmar-contrasenya"
            name="confirmar_contrasenya"
            type="password"
            autocomplete="new-password"
            placeholder="Repeteix la contrasenya"
            aria-describedby="confirmar-contrasenya-error"
          />
          <p
            id="confirmar-contrasenya-error"
            class="register-form__error"
            aria-live="polite"
          ></p>
        </div>

        <label class="register-form__terms" for="accepta-termes">
          <input id="accepta-termes" name="accepta_termes" type="checkbox" />
          <span>
            Accepto els
            <a href="#" @click.prevent>termes d'ús</a>
            i la
            <a href="#" @click.prevent>política de privacitat</a>.
          </span>
        </label>

        <button class="register-form__submit" type="submit">
          Completar Registre
          <span aria-hidden="true">→</span>
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.register-page {
  position: relative;
  display: flex;
  min-height: 100svh;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  box-sizing: border-box;
  background-position: center;
  background-size: cover;
  overflow: auto;
}

.register-page__overlay {
  position: fixed;
  inset: 0;
  background: rgb(25 26 31 / 58%);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.register-modal {
  position: relative;
  z-index: 1;
  width: min(100%, 360px);
  max-height: calc(100svh - 2rem);
  box-sizing: border-box;
  overflow-y: auto;
  padding: 1.45rem;
  border-radius: 0.7rem;
  color: #4d4541;
  background: #fffdf8;
  box-shadow: 0 1.2rem 3rem rgb(0 0 0 / 30%);
}

.register-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.register-modal__welcome {
  margin: 0 0 0.25rem;
  color: #756d66;
  font-size: 0.58rem;
  font-weight: 700;
}

.register-modal h1 {
  margin: 0;
  color: #442d2a;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.register-modal__close {
  display: grid;
  width: 1.7rem;
  height: 1.7rem;
  flex: 0 0 1.7rem;
  place-items: center;
  padding: 0;
  border: 1px solid #e5dcd0;
  border-radius: 0.45rem;
  color: #8d8177;
  background: transparent;
  cursor: pointer;
  font-size: 1.35rem;
  font-weight: 300;
  line-height: 1;
}

.register-modal__close:hover,
.register-modal__close:focus-visible {
  color: #870000;
  border-color: #870000;
}

.register-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.2rem;
  margin-bottom: 1.1rem;
  padding: 0.2rem;
  border-radius: 0.45rem;
  background: #f3ecdf;
}

.register-tabs__tab {
  min-height: 2.1rem;
  padding: 0.45rem 0.35rem;
  border: 0;
  border-radius: 0.35rem;
  color: #837a72;
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 700;
}

.register-tabs__tab--active {
  color: #a00000;
  background: #fffdf8;
  box-shadow: 0 1px 4px rgb(91 47 22 / 14%);
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.account-type {
  margin: 0 0 0.45rem;
  padding: 0;
  border: 0;
}

.account-type legend {
  margin-bottom: 0.65rem;
  color: #4d4541;
  font-size: 0.62rem;
  font-weight: 700;
}

.account-type__options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.35rem;
}

.account-type__option {
  display: flex;
  min-height: 2.2rem;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.35rem 0.2rem;
  border: 1px solid #e4d9cd;
  border-radius: 0.4rem;
  color: #6f6862;
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 0.58rem;
  font-weight: 700;
}

.account-type__option span {
  font-size: 0.85rem;
  font-weight: 400;
}

.account-type__option--active {
  border: 2px solid #a00000;
  color: #850000;
  background: #f8edda;
}

.register-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.register-form__field label {
  color: #4d4541;
  font-size: 0.62rem;
  font-weight: 700;
}

.register-form__field input {
  box-sizing: border-box;
  width: 100%;
  min-height: 2rem;
  padding: 0.5rem 0.65rem;
  border: 1px solid #e1d8cd;
  border-radius: 0.35rem;
  color: #4d4541;
  background: #fff;
  font: inherit;
  font-size: 0.63rem;
}

.register-form__field input::placeholder {
  color: #aea7a0;
}

.register-form__field input:focus {
  outline: 2px solid #a00000;
  outline-offset: 1px;
}

.register-form__help {
  margin: 0;
  color: #989089;
  font-size: 0.5rem;
}

.register-form__error {
  min-height: 0;
  margin: 0;
  color: #a00000;
  font-size: 0.55rem;
}

.register-form__terms {
  display: flex;
  align-items: flex-start;
  gap: 0.35rem;
  margin-top: 0.05rem;
  color: #827a73;
  font-size: 0.55rem;
  line-height: 1.35;
}

.register-form__terms input {
  width: 0.75rem;
  height: 0.75rem;
  flex: 0 0 auto;
  margin: 0.05rem 0 0;
  accent-color: #a00000;
}

.register-form__terms a {
  color: inherit;
  text-decoration: underline;
}

.register-form__submit {
  display: flex;
  min-height: 2.1rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.05rem;
  padding: 0.5rem 1rem;
  border: 0;
  border-radius: 0.35rem;
  color: #fff;
  background: #a00000;
  box-shadow: 0 0.2rem 0.35rem rgb(91 0 0 / 20%);
  cursor: pointer;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 700;
}

.register-form__submit:hover,
.register-form__submit:focus-visible {
  background: #850000;
}

.register-form__submit:focus-visible,
.account-type__option:focus-visible,
.register-tabs__tab:focus-visible {
  outline: 2px solid #a00000;
  outline-offset: 2px;
}

.register-form__submit span {
  font-size: 1rem;
  font-weight: 400;
}

@media (max-width: 420px) {
  .register-page {
    align-items: flex-start;
    padding: 0.6rem;
  }

  .register-modal {
    max-height: calc(100svh - 1.2rem);
    padding: 1.1rem;
  }

  .account-type__option {
    font-size: 0.52rem;
  }
}
</style>
