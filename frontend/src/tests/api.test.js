import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useSessioStore } from "../stores/sessio.js";

const mocks = vi.hoisted(() => ({
  requestUse: vi.fn(),
  responseUse: vi.fn(),
  refreshPost: vi.fn(),
}));

vi.mock("axios", () => {
  const apiClient = vi.fn();
  Object.assign(apiClient, {
    interceptors: {
      request: { use: mocks.requestUse },
      response: { use: mocks.responseUse },
    },
  });
  apiClient.mockResolvedValue({ data: "ok" });
  const refreshClient = { post: mocks.refreshPost };

  return {
    default: {
      create: vi.fn()
        .mockReturnValueOnce(apiClient)
        .mockReturnValueOnce(refreshClient),
    },
  };
});

const { default: api } = await import("../services/api.js");

describe("client HTTP", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.refreshPost.mockReset();
    api.mockClear();
  });

  it("afegeix el token d'accés a les peticions", () => {
    const sessio = useSessioStore();
    sessio.iniciarSessio({ accessToken: "access" });
    const interceptor = mocks.requestUse.mock.calls[0][0];
    const config = { headers: {} };

    expect(interceptor(config)).toMatchObject({
      headers: { Authorization: expect.stringContaining("Bearer") },
    });
  });

  it("renova el token i repeteix una petició que ha expirat", async () => {
    const sessio = useSessioStore();
    sessio.iniciarSessio({
      accessToken: "antic",
      refreshToken: "refresh",
    });
    mocks.refreshPost.mockResolvedValue({
      data: { access: "nou", refresh: "nou-refresh" },
    });
    const [, interceptorError] = mocks.responseUse.mock.calls[0];
    const config = { headers: {}, _reintentat: false };
    const resposta = await interceptorError({
      response: { status: 401 },
      config,
    });

    expect(mocks.refreshPost).toHaveBeenCalledWith("/auth/refresh/", {
      refresh: "refresh",
    });
    expect(sessio.accessToken).toBe("nou");
    expect(config.headers.Authorization).toEqual(
      expect.stringContaining("Bearer"),
    );
    expect(api).toHaveBeenCalledWith(config);
    expect(resposta).toEqual({ data: "ok" });
  });
});
