import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthContext } from "@/app/auth-provider";
import { ThemeProvider } from "@/app/theme-provider";
import { AppSidebar } from "@/components/layout/dashboard-layout";

vi.mock("@/app/auth-provider", () => ({
  useAuthContext: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuthContext);

function renderSidebar() {
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <AppSidebar collapsed={false} onToggle={() => undefined} />
      </ThemeProvider>
    </MemoryRouter>,
  );
}

describe("AppSidebar", () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it("hides admin nav for regular users", () => {
    mockedUseAuth.mockReturnValue({
      user: { id: "1", email: "user@example.com", full_name: "User", role: "user" },
    } as ReturnType<typeof useAuthContext>);

    renderSidebar();
    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
    expect(screen.getByText("Chat")).toBeInTheDocument();
  });

  it("shows admin nav for platform admins", () => {
    mockedUseAuth.mockReturnValue({
      user: {
        id: "1",
        email: "admin@example.com",
        full_name: "Admin",
        role: "platform_admin",
      },
    } as ReturnType<typeof useAuthContext>);

    renderSidebar();
    expect(screen.getByRole("link", { name: /admin/i })).toBeInTheDocument();
  });
});
