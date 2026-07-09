import { Navigate } from "react-router-dom";
import { type ReactNode } from "react";

import { useAuthContext } from "@/app/auth-provider";
import { PageSkeleton } from "@/components/layout/page-skeleton";

export function AdminGuard({ children }: { children: ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuthContext();

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== "platform_admin") {
    return <Navigate to="/app" replace />;
  }

  return children;
}
