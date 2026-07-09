import { describe, expect, it } from "vitest";

import { mainNavItems } from "@/lib/navigation";

describe("navigation", () => {
  it("includes core app routes", () => {
    const hrefs = mainNavItems.map((item) => item.href);
    expect(hrefs).toEqual([
      "/app",
      "/app/chat",
      "/app/knowledge",
      "/app/organizations",
      "/app/search",
      "/app/settings",
      "/app/admin",
    ]);
  });

  it("marks only admin route as admin-only", () => {
    const adminItems = mainNavItems.filter((item) => item.adminOnly);
    expect(adminItems).toHaveLength(1);
    expect(adminItems[0]?.href).toBe("/app/admin");
  });
});
