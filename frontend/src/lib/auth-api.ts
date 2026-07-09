import { api } from "@/lib/api";
import { getRefreshToken } from "@/lib/auth-storage";
import type {
  AuthResponse,
  ForgotPasswordPayload,
  LoginPayload,
  ResetPasswordPayload,
  SignupPayload,
  User,
} from "@/types/auth";

export type ProfileUpdatePayload = {
  full_name?: string | null;
  avatar_url?: string | null;
};

export async function loginRequest(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function signupRequest(payload: SignupPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/signup", payload);
  return data;
}

export async function logoutRequest(): Promise<void> {
  const refreshToken = getRefreshToken();
  await api.post("/auth/logout", { refresh_token: refreshToken });
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function updateProfileRequest(payload: ProfileUpdatePayload): Promise<User> {
  const { data } = await api.patch<User>("/auth/me", payload);
  return data;
}

export async function forgotPasswordRequest(payload: ForgotPasswordPayload): Promise<void> {
  await api.post("/auth/forgot-password", payload);
}

export async function resetPasswordRequest(payload: ResetPasswordPayload): Promise<void> {
  await api.post("/auth/reset-password", payload);
}
