import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminGuard } from "@/app/admin-guard";
import { useAuthContext } from "@/app/auth-provider";

vi.mock("@/app/auth-provider", () => ({
  useAuthContext: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuthContext);

function renderAdminRoute(initialEntry = "/app/admin") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          path="/app/admin"
          element={
            <AdminGuard>
              <div>Admin panel</div>
            </AdminGuard>
          }
        />
        <Route path="/app" element={<div>Dashboard</div>} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AdminGuard", () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it("shows skeleton while auth is loading", () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
    } as ReturnType<typeof useAuthContext>);

    renderAdminRoute();
    expect(screen.queryByText("Admin panel")).not.toBeInTheDocument();
    expect(document.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("redirects unauthenticated users to login", () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    } as ReturnType<typeof useAuthContext>);

    renderAdminRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects non-admin users to dashboard", () => {
    mockedUseAuth.mockReturnValue({
      user: { id: "1", email: "user@example.com", full_name: "User", role: "user" },
      isAuthenticated: true,
      isLoading: false,
    } as ReturnType<typeof useAuthContext>);

    renderAdminRoute();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders children for platform admins", () => {
    mockedUseAuth.mockReturnValue({
      user: {
        id: "1",
        email: "admin@example.com",
        full_name: "Admin",
        role: "platform_admin",
      },
      isAuthenticated: true,
      isLoading: false,
    } as ReturnType<typeof useAuthContext>);

    renderAdminRoute();
    expect(screen.getByText("Admin panel")).toBeInTheDocument();
  });
});
