import { describe, expect, it } from "vitest";
import { esEnllacValid, esIsbnValid } from "../utils/validacions.js";

describe("validació de l'ISBN", () => {
  it.each([
    ["ISBN-13", "9788466421126"],
    ["ISBN-13 amb guions", "978-84-664-2112-6"],
    ["ISBN-13 amb espais", "978 84 664 2112 6"],
    ["ISBN-10", "0306406152"],
    ["ISBN-10 acabat en X", "080442957X"],
    ["ISBN-10 acabat en x minúscula", "080442957x"],
  ])("accepta un %s", (_, isbn) => {
    expect(esIsbnValid(isbn)).toBe(true);
  });

  it.each([
    ["un dígit de control incorrecte", "9788466421127"],
    ["un ISBN-10 incorrecte", "0306406153"],
    ["un ISBN-13 que no comença per 978 o 979", "9778466421126"],
    ["massa xifres", "97884664211260"],
    ["lletres", "97884664ABCDE"],
    ["un text buit", ""],
  ])("rebutja %s", (_, isbn) => {
    expect(esIsbnValid(isbn)).toBe(false);
  });
});

describe("validació de l'enllaç de la portada", () => {
  it("accepta enllaços http i https", () => {
    expect(esEnllacValid("https://example.com/portada.jpg")).toBe(true);
    expect(esEnllacValid("http://example.com/portada.jpg")).toBe(true);
  });

  it("rebutja altres esquemes i textos que no són enllaços", () => {
    expect(esEnllacValid("ftp://example.com/portada.jpg")).toBe(false);
    expect(esEnllacValid("javascript:alert(1)")).toBe(false);
    expect(esEnllacValid("portada.jpg")).toBe(false);
  });
});
