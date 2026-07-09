export type User = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active?: boolean;
  is_verified?: boolean;
  avatar_url?: string | null;
};

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type SignupPayload = {
  email: string;
  password: string;
  full_name?: string;
};

export type ForgotPasswordPayload = {
  email: string;
};

export type ResetPasswordPayload = {
  token: string;
  password: string;
};

export type AuthResponse = AuthTokens & {
  user: User;
};
