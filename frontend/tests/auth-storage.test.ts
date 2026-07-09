import { describe, expect, it } from "vitest";

import {
  clearAuth,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  persistAuth,
  type StoredUser,
} from "@/lib/auth-storage";

const user: StoredUser = {
  id: "user-1",
  email: "alice@example.com",
  full_name: "Alice",
  role: "user",
};

describe("auth-storage", () => {
  it("persists and reads auth tokens and user", () => {
    persistAuth("access-abc", "refresh-xyz", user);

    expect(getAccessToken()).toBe("access-abc");
    expect(getRefreshToken()).toBe("refresh-xyz");
    expect(getStoredUser()).toEqual(user);
  });

  it("clears persisted auth", () => {
    persistAuth("access-abc", "refresh-xyz", user);
    clearAuth();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(getStoredUser()).toBeNull();
  });

  it("returns null for corrupted user JSON", () => {
    localStorage.setItem("kb_user", "{not-json");
    expect(getStoredUser()).toBeNull();
  });
});
