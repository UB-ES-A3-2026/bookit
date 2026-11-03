import { afterEach } from "vitest";

afterEach(() => {
  sessionStorage.clear();
  document.body.innerHTML = "";
});
