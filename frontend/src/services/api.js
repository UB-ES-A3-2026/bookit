import axios from "axios";
import { useSessioStore } from "../stores/sessio.js";

const API_BASE_URL = import.meta.env?.VITE_API_URL ?? "/api";
const REFRESH_ENDPOINT = "/auth/token/refresh/";

const api = axios.create({
  baseURL: API_BASE_URL,
});

const clientRefresh = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const sessio = useSessioStore();

  if (sessio.accessToken) {
    config.headers.Authorization = `Bearer ${sessio.accessToken}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const configOriginal = error.config;
    const sessio = useSessioStore();

    if (
      error.response?.status !== 401 ||
      configOriginal?._reintentat ||
      !sessio.refreshToken
    ) {
      return Promise.reject(error);
    }

    configOriginal._reintentat = true;

    try {
      const resposta = await clientRefresh.post(REFRESH_ENDPOINT, {
        refresh: sessio.refreshToken,
      });
      const { access, refresh } = resposta.data;

      sessio.actualitzarToken(access, refresh ?? sessio.refreshToken);
      configOriginal.headers.Authorization = `Bearer ${access}`;

      return api(configOriginal);
    } catch (errorRenovacio) {
      sessio.tancarSessio();
      return Promise.reject(errorRenovacio);
    }
  },
);

export default api;
