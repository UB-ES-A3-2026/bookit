import { afterEach } from "vitest";

afterEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  document.body.innerHTML = "";
});
