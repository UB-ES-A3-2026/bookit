import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import router, { titolPestanya } from "../router";

const arrel = resolve(__dirname, "../..");

describe("text de la pestanya", () => {
  it("combina el títol de la vista amb el nom de l'aplicació", () => {
    expect(titolPestanya({ meta: { titol: "Inicia sessió" } })).toBe("Inicia sessió · bookit");
  });

  it("mostra només el nom de l'aplicació si la ruta no té títol", () => {
    expect(titolPestanya({ meta: {} })).toBe("bookit");
    expect(titolPestanya({})).toBe("bookit");
  });

  it("dona un títol propi a cada vista", () => {
    const titols = router.getRoutes().map((ruta) => ruta.meta.titol);

    titols.forEach((titol) => expect(titol).toBeTruthy());
    expect(new Set(titols).size).toBe(titols.length);
  });

  it("actualitza el document en navegar", async () => {
    await router.push("/inicia-sessio");
    expect(document.title).toBe("Inicia sessió · bookit");

    await router.push("/cerca");
    expect(document.title).toBe("Resultats de la cerca · bookit");
  });
});

describe("favicon", () => {
  it("fa servir el logo de bookit en lloc del de Vite", () => {
    const html = readFileSync(resolve(arrel, "index.html"), "utf-8");

    expect(html).toContain('<link rel="icon" type="image/png" href="/favicon.png" />');
    expect(html).toContain("<title>bookit</title>");
    expect(readFileSync(resolve(arrel, "public/favicon.png")).length).toBeGreaterThan(0);
  });
});
