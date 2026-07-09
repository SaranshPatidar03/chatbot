import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import { type ReactElement, type ReactNode } from "react";
import { MemoryRouter, type MemoryRouterProps } from "react-router-dom";

import { AuthProvider } from "@/app/auth-provider";
import { ThemeProvider } from "@/app/theme-provider";

type TestProvidersProps = {
  children: ReactNode;
  routerProps?: MemoryRouterProps;
  withAuth?: boolean;
};

function TestProviders({ children, routerProps, withAuth = false }: TestProvidersProps) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const content = withAuth ? <AuthProvider>{children}</AuthProvider> : children;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <MemoryRouter {...routerProps}>{content}</MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

type CustomRenderOptions = Omit<RenderOptions, "wrapper"> & {
  routerProps?: MemoryRouterProps;
  withAuth?: boolean;
};

export function renderWithProviders(ui: ReactElement, options: CustomRenderOptions = {}) {
  const { routerProps, withAuth, ...renderOptions } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <TestProviders routerProps={routerProps} withAuth={withAuth}>
        {children}
      </TestProviders>
    ),
    ...renderOptions,
  });
}
