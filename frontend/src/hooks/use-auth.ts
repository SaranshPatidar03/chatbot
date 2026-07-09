import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import {
  fetchCurrentUser,
  forgotPasswordRequest,
  loginRequest,
  logoutRequest,
  resetPasswordRequest,
  signupRequest,
} from "@/lib/auth-api";
import { clearAuth, getAccessToken, getStoredUser, persistAuth } from "@/lib/auth-storage";
import { queryKeys } from "@/lib/query-keys";
import type { User } from "@/types/auth";

export function useAuth() {
  const queryClient = useQueryClient();
  const token = getAccessToken();

  const userQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: fetchCurrentUser,
    enabled: Boolean(token),
    retry: false,
    initialData: () => {
      const stored = getStoredUser();
      return stored as User | undefined;
    },
  });

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => {
      persistAuth(data.access_token, data.refresh_token, data.user);
      queryClient.setQueryData(queryKeys.me, data.user);
    },
  });

  const signupMutation = useMutation({
    mutationFn: signupRequest,
    onSuccess: (data) => {
      persistAuth(data.access_token, data.refresh_token, data.user);
      queryClient.setQueryData(queryKeys.me, data.user);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logoutRequest,
    onSettled: () => {
      clearAuth();
      queryClient.removeQueries({ queryKey: queryKeys.me });
    },
  });

  const forgotPasswordMutation = useMutation({
    mutationFn: forgotPasswordRequest,
  });

  const resetPasswordMutation = useMutation({
    mutationFn: resetPasswordRequest,
  });

  const logout = useCallback(() => logoutMutation.mutate(), [logoutMutation]);

  const isAuthenticated = Boolean(token && (userQuery.data || getStoredUser()));

  return {
    user: userQuery.data ?? getStoredUser(),
    isAuthenticated,
    isLoading: userQuery.isLoading && Boolean(token),
    login: loginMutation.mutateAsync,
    signup: signupMutation.mutateAsync,
    logout,
    forgotPassword: forgotPasswordMutation.mutateAsync,
    resetPassword: resetPasswordMutation.mutateAsync,
    loginError: loginMutation.error,
    signupError: signupMutation.error,
    isLoggingIn: loginMutation.isPending,
    isSigningUp: signupMutation.isPending,
    refetchUser: userQuery.refetch,
  };
}
