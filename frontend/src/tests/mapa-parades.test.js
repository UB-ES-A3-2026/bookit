import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import MapaParades from "../components/MapaParades.vue";

// US12-T7: parades de la ruta sobre un mapa (Leaflet amb el mapa base de l'ICGC).
const TIPUS = { recollida: "Recollida", lliurament: "Lliurament" };

function llocDe(parada) {
  return parada.tipus === "recollida" ? parada.adreca.biblioteca.nom : parada.adreca.text;
}

function parada(id, ordre, tipus, latitud, longitud, text = "C/ Major 1") {
  return {
    id,
    ordre,
    tipus,
    comanda: 12,
    estat: "preparada",
    llibres: [],
    adreca:
      tipus === "recollida"
        ? { biblioteca: { id: 3, nom: "Biblioteca Central" }, text: null, latitud, longitud }
        : { biblioteca: null, text, latitud, longitud },
  };
}

const ruta = () => [
  parada(18, 1, "recollida", 41.386016, 2.169408),
  parada(19, 2, "lliurament", 41.403629, 2.174355),
  parada(20, 3, "recollida", 41.380, 2.150),
];

let wrapper;

async function renderitza(parades) {
  wrapper = mount(MapaParades, {
    props: { parades, llocDe, tipus: TIPUS },
    attachTo: document.body,
  });
  await flushPromises();
}

const marcadors = () => [...document.querySelectorAll(".marcador-parada")];

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
});

describe("mapa de les parades", () => {
  it("mostra el mapa amb un marcador numerat per parada, en ordre", async () => {
    await renderitza(ruta());

    expect(wrapper.find('[data-testid="mapa-parades"]').exists()).toBe(true);
    expect(marcadors().map((element) => element.textContent)).toEqual(["1", "2", "3"]);
    expect(marcadors().map((element) => element.getAttribute("title"))).toEqual([
      "Parada 1: Recollida",
      "Parada 2: Lliurament",
      "Parada 3: Recollida",
    ]);
    expect(wrapper.find(".avis-mapa").exists()).toBe(false);
  });

  it("distingeix les recollides dels lliuraments", async () => {
    await renderitza(ruta());

    expect(marcadors()[0].classList).toContain("marcador-recollida");
    expect(marcadors()[1].classList).toContain("marcador-lliurament");
  });

  it("acredita el mapa base de l'ICGC", async () => {
    await renderitza(ruta());

    expect(document.querySelector(".leaflet-control-attribution").textContent).toContain(
      "Institut Cartogràfic i Geològic de Catalunya",
    );
  });

  it("accepta les coordenades enviades com a text", async () => {
    await renderitza([parada(18, 1, "recollida", "41.386016", "2.169408")]);

    expect(marcadors()).toHaveLength(1);
  });

  it("la finestra de cada marcador mostra el tipus i el lloc sense interpretar HTML", async () => {
    await renderitza([
      parada(19, 1, "lliurament", 41.4, 2.17, "<img src=x onerror=alert(1)> C/ Major 1"),
    ]);

    marcadors()[0].dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await flushPromises();

    const finestra = document.querySelector(".leaflet-popup-content");
    expect(finestra.textContent).toContain("1. Lliurament");
    expect(finestra.textContent).toContain("<img src=x onerror=alert(1)> C/ Major 1");
    expect(finestra.querySelector("img")).toBeNull();
  });
});

describe("parades sense ubicació", () => {
  it("no situa les parades sense coordenades i avisa que n'hi ha una", async () => {
    await renderitza([...ruta().slice(0, 2), parada(20, 3, "recollida", null, null)]);

    expect(marcadors().map((element) => element.textContent)).toEqual(["1", "2"]);
    expect(wrapper.find(".avis-mapa").text()).toBe(
      "1 parada no surt al mapa perquè no en tenim la ubicació. La tens a la llista.",
    );
  });

  it("fa servir el plural quan en falten diverses", async () => {
    await renderitza([
      parada(18, 1, "recollida", 41.38, 2.16),
      parada(19, 2, "lliurament", null, 2.17),
      parada(20, 3, "recollida", "", ""),
    ]);

    expect(marcadors()).toHaveLength(1);
    expect(wrapper.find(".avis-mapa").text()).toBe(
      "2 parades no surten al mapa perquè no en tenim la ubicació. Les tens a la llista.",
    );
  });

  it("descarta coordenades que no són números", async () => {
    await renderitza([parada(18, 1, "recollida", "no", "vàlida")]);

    expect(marcadors()).toHaveLength(0);
  });

  it("sense cap ubicació no mostra el mapa i ho explica", async () => {
    await renderitza(ruta().map((element) => ({
      ...element,
      adreca: { ...element.adreca, latitud: null, longitud: null },
    })));

    expect(wrapper.find('[data-testid="mapa-parades"]').exists()).toBe(false);
    expect(document.querySelector(".leaflet-container")).toBeNull();
    expect(wrapper.find(".avis-mapa").text()).toBe(
      "Encara no tenim la ubicació de cap parada, per això no es pot mostrar el mapa. Les tens totes a la llista.",
    );
  });

  it("sense parades no mostra res", async () => {
    await renderitza([]);

    expect(wrapper.find(".mapa-parades").exists()).toBe(false);
  });
});

describe("canvis de les parades", () => {
  it("actualitza els marcadors quan canvia la ruta", async () => {
    await renderitza(ruta());

    await wrapper.setProps({ parades: ruta().slice(0, 1) });
    await flushPromises();

    expect(marcadors().map((element) => element.textContent)).toEqual(["1"]);
  });

  it("crea el mapa quan arriben les primeres coordenades i el treu si desapareixen", async () => {
    await renderitza([parada(18, 1, "recollida", null, null)]);
    expect(document.querySelector(".leaflet-container")).toBeNull();

    await wrapper.setProps({ parades: ruta() });
    await flushPromises();
    expect(document.querySelector(".leaflet-container")).not.toBeNull();
    expect(marcadors()).toHaveLength(3);

    await wrapper.setProps({ parades: [parada(18, 1, "recollida", null, null)] });
    await flushPromises();
    expect(document.querySelector(".leaflet-container")).toBeNull();
  });

  it("allibera el mapa en desmuntar el component", async () => {
    await renderitza(ruta());

    wrapper.unmount();
    wrapper = undefined;

    expect(document.querySelector(".leaflet-container")).toBeNull();
  });
});
