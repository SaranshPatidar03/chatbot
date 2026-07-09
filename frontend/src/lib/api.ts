import axios from "axios";

import { clearAuth, getAccessToken, getRefreshToken, persistAuth, getStoredUser } from "@/lib/auth-storage";
import { refreshTokenRequest } from "@/lib/token-refresh";

const rawBase = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const api = axios.create({
  baseURL: rawBase ?? "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (!original || original._retry) {
      return Promise.reject(error);
    }

    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuth();
        return Promise.reject(error);
      }

      if (!refreshPromise) {
        refreshPromise = refreshTokenRequest(refreshToken)
          .then((tokens) => {
            const user = getStoredUser();
            if (user) {
              persistAuth(tokens.access_token, tokens.refresh_token, user);
            }
            return tokens.access_token;
          })
          .catch(() => {
            clearAuth();
            return null;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newToken = await refreshPromise;
      if (!newToken) {
        return Promise.reject(error);
      }

      original._retry = true;
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    }

    return Promise.reject(error);
  },
);

declare module "axios" {
  export interface AxiosRequestConfig {
    _retry?: boolean;
  }
}
