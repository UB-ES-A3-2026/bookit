import { defineStore } from "pinia";

const SESSION_STORAGE_KEY = "bookit.sessio";

function llegirSessio() {
  const sessioDesada = sessionStorage.getItem(SESSION_STORAGE_KEY);

  if (!sessioDesada) {
    return {
      accessToken: null,
      refreshToken: null,
      usuari: null,
      rol: null,
    };
  }

  try {
    const sessio = JSON.parse(sessioDesada);

    return {
      accessToken: sessio.accessToken ?? null,
      refreshToken: sessio.refreshToken ?? null,
      usuari: sessio.usuari ?? null,
      rol: sessio.rol ?? null,
    };
  } catch {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    return {
      accessToken: null,
      refreshToken: null,
      usuari: null,
      rol: null,
    };
  }
}

function desarSessio(sessio) {
  sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessio));
}

export const useSessioStore = defineStore("sessio", {
  state: () => llegirSessio(),

  getters: {
    autenticat: (state) => Boolean(state.accessToken),
  },

  actions: {
    iniciarSessio({ accessToken, refreshToken = null, usuari = null, rol = null }) {
      if (!accessToken) {
        throw new Error("Cal proporcionar un token d'accés per iniciar sessió.");
      }

      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      this.usuari = usuari;
      this.rol = rol;

      desarSessio({
        accessToken: this.accessToken,
        refreshToken: this.refreshToken,
        usuari: this.usuari,
        rol: this.rol,
      });
    },

    tancarSessio() {
      this.accessToken = null;
      this.refreshToken = null;
      this.usuari = null;
      this.rol = null;
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    },
  },
});
