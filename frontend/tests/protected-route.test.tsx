import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthContext } from "@/app/auth-provider";
import { GuestRoute, ProtectedRoute } from "@/app/protected-route";

vi.mock("@/app/auth-provider", () => ({
  useAuthContext: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuthContext);

describe("ProtectedRoute", () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it("redirects guests to login with return path", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    } as ReturnType<typeof useAuthContext>);

    render(
      <MemoryRouter initialEntries={["/app/settings"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app/settings" element={<div>Settings</div>} />
          </Route>
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders protected content for authenticated users", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "user@example.com", full_name: "User", role: "user" },
    } as ReturnType<typeof useAuthContext>);

    render(
      <MemoryRouter initialEntries={["/app/settings"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/app/settings" element={<div>Settings</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });
});

describe("GuestRoute", () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it("redirects authenticated users away from auth pages", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "user@example.com", full_name: "User", role: "user" },
    } as ReturnType<typeof useAuthContext>);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<div>Login form</div>} />
          </Route>
          <Route path="/app" element={<div>Dashboard</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("allows guests to view auth pages", () => {
    mockedUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    } as ReturnType<typeof useAuthContext>);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<div>Login form</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login form")).toBeInTheDocument();
  });
});
