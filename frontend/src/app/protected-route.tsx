import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthContext } from "@/app/auth-provider";
import { PageSkeleton } from "@/components/layout/page-skeleton";

type ProtectedRouteProps = {
  adminOnly?: boolean;
};

export function ProtectedRoute({ adminOnly = false }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  const location = useLocation();

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (adminOnly && user?.role !== "platform_admin") {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}

export function GuestRoute() {
  const { isAuthenticated, isLoading } = useAuthContext();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  return <Outlet />;
}
