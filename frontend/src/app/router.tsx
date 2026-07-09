import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { GuestRoute, ProtectedRoute } from "@/app/protected-route";
import { AdminGuard } from "@/app/admin-guard";
import { AuthLayout } from "@/components/layout/auth-layout";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { PublicLayout } from "@/components/layout/public-layout";
import { AdminPage } from "@/features/admin/admin-page";
import { ForgotPasswordPage } from "@/features/auth/forgot-password-page";
import { LoginPage } from "@/features/auth/login-page";
import { ResetPasswordPage } from "@/features/auth/reset-password-page";
import { SignupPage } from "@/features/auth/signup-page";
import { VerifyEmailPage } from "@/features/auth/verify-email-page";
import { ChatPage } from "@/features/chat/chat-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { LandingPage } from "@/features/dashboard/landing-page";
import { KnowledgePage } from "@/features/knowledge/knowledge-page";
import { OrganizationDetailPage } from "@/features/organizations/organization-detail-page";
import { OrganizationsPage } from "@/features/organizations/organizations-page";
import { SearchPage } from "@/features/search/search-page";
import { SettingsPage } from "@/features/settings/settings-page";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";

function AppRoutes() {
  useKeyboardShortcuts();

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<LandingPage />} />
      </Route>

      <Route element={<GuestRoute />}>
        <Route element={<AuthLayout />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="signup" element={<SignupPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
          <Route path="verify-email" element={<VerifyEmailPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="app" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:chatId" element={<ChatPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="organizations" element={<OrganizationsPage />} />
          <Route path="organizations/:orgId" element={<OrganizationDetailPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route
            path="admin"
            element={
              <AdminGuard>
                <AdminPage />
              </AdminGuard>
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
