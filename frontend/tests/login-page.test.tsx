import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthContext } from "@/app/auth-provider";
import { LoginPage } from "@/features/auth/login-page";
import { renderWithProviders } from "./test-utils";

vi.mock("@/app/auth-provider", () => ({
  useAuthContext: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuthContext);

describe("LoginPage", () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it("submits credentials and navigates to the app", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    mockedUseAuth.mockReturnValue({
      login,
      isLoggingIn: false,
    } as ReturnType<typeof useAuthContext>);

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { routerProps: { initialEntries: ["/login"] } });

    await user.type(screen.getByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Password"), "securepass123");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        email: "alice@example.com",
        password: "securepass123",
      });
    });
  });

  it("shows API error messages", async () => {
    const error = new AxiosError("Unauthorized");
    error.response = {
      data: { detail: "Invalid credentials" },
      status: 401,
      statusText: "Unauthorized",
      headers: {},
      config: {} as never,
    };
    const login = vi.fn().mockRejectedValue(error);
    mockedUseAuth.mockReturnValue({
      login,
      isLoggingIn: false,
    } as ReturnType<typeof useAuthContext>);

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { routerProps: { initialEntries: ["/login"] } });

    await user.type(screen.getByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
  });
});
