import { expect, test } from "@playwright/test";

test("landing page shows product headline and auth links", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main").getByText("Knowledge Chatbot", { exact: true })).toBeVisible();
  await expect(page.getByRole("main").getByRole("link", { name: "Get started" })).toHaveAttribute("href", "/signup");
  await expect(page.getByRole("main").getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
  await expect(page.getByRole("main").getByText("Your documents only")).toBeVisible();
});

test("login page renders sign-in form", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("signup page renders registration form", async ({ page }) => {
  await page.goto("/signup");
  await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
});
