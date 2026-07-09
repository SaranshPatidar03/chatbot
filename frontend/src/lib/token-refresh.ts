import axios from "axios";

import type { AuthTokens } from "@/types/auth";

const rawBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
const baseURL = rawBase ?? "/api/v1";

/** Refresh tokens without going through the main API interceptor (avoids loops). */
export async function refreshTokenRequest(refreshToken: string): Promise<AuthTokens> {
  const { data } = await axios.post<AuthTokens>(`${baseURL}/auth/refresh`, {
    refresh_token: refreshToken,
  });
  return data;
}
