import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useSessioStore } from "../stores/sessio.js";

describe("store de sessió", () => {
  beforeEach(() => {
    sessionStorage.clear();
    setActivePinia(createPinia());
  });

  it("desa i recupera els tokens i el perfil", () => {
    const sessio = useSessioStore();
    const usuari = { id: 1, nom: "Joan", rol: "usuari" };

    sessio.iniciarSessio({
      accessToken: "access",
      refreshToken: "refresh",
      usuari,
      rol: "usuari",
    });

    expect(sessio.autenticat).toBe(true);
    expect(JSON.parse(sessionStorage.getItem("bookit.sessio"))).toEqual({
      accessToken: "access",
      refreshToken: "refresh",
      usuari,
      rol: "usuari",
    });
  });

  it("actualitza el token i tanca la sessió", () => {
    const sessio = useSessioStore();
    sessio.iniciarSessio({ accessToken: "antic", refreshToken: "refresh" });

    sessio.actualitzarToken("nou");
    expect(sessio.accessToken).toBe("nou");
    expect(sessio.refreshToken).toBe("refresh");

    sessio.tancarSessio();
    expect(sessio.autenticat).toBe(false);
    expect(sessionStorage.getItem("bookit.sessio")).toBeNull();
  });
});
