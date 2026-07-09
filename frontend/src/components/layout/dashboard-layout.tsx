import { Link, NavLink, Outlet } from "react-router-dom";
import {
  LogOut,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Sun,
  X,
} from "lucide-react";
import { useState } from "react";

import { useAuthContext } from "@/app/auth-provider";
import { useTheme } from "@/app/theme-provider";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { mainNavItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function AppSidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const { user } = useAuthContext();
  const isAdmin = user?.role === "platform_admin";

  const items = mainNavItems.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-border/70 bg-card/40 backdrop-blur-sm transition-all duration-300",
        collapsed ? "w-[72px]" : "w-64",
      )}
    >
      <div className="flex h-14 items-center justify-between px-3">
        {!collapsed ? (
          <Link to="/app" className="truncate font-display text-sm font-bold text-primary">
            Knowledge Chatbot
          </Link>
        ) : (
          <span className="mx-auto font-display text-sm font-bold text-primary">KB</span>
        )}
        <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </Button>
      </div>
      <Separator />
      <nav className="flex-1 space-y-1 p-2">
        {items.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            end={item.href === "/app"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed ? (
              <>
                <span className="flex-1">{item.label}</span>
                {item.shortcut ? (
                  <Badge variant="muted" className="hidden xl:inline-flex">
                    {item.shortcut}
                  </Badge>
                ) : null}
              </>
            ) : null}
          </NavLink>
        ))}
      </nav>
      {!collapsed && user ? (
        <div className="border-t border-border/70 p-3">
          <div className="flex items-center gap-2">
            <Avatar name={user.full_name ?? user.email} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user.full_name ?? "User"}</p>
              <p className="truncate text-xs text-muted-foreground">{user.email}</p>
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  );
}

export function AppHeader({
  onOpenMobileNav,
  showMobileMenu,
}: {
  onOpenMobileNav: () => void;
  showMobileMenu: boolean;
}) {
  const { theme, toggleTheme } = useTheme();
  const { logout } = useAuthContext();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/70 bg-background/70 px-4 backdrop-blur-md">
      <div className="flex items-center gap-2 lg:hidden">
        <Button variant="ghost" size="icon" onClick={onOpenMobileNav} aria-label="Open navigation">
          {showMobileMenu ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </Button>
        <span className="font-display text-sm font-bold">Knowledge Chatbot</span>
      </div>
      <div className="hidden text-sm text-muted-foreground lg:block">
        Grounded answers from your knowledge base
      </div>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={toggleTheme}>
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button variant="ghost" size="icon" aria-label="Sign out" onClick={() => logout()}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}

export function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden lg:block">
        <AppSidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      </div>
      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative z-50 h-full w-64">
            <AppSidebar collapsed={false} onToggle={() => setMobileOpen(false)} />
          </div>
        </div>
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader
          showMobileMenu={mobileOpen}
          onOpenMobileNav={() => setMobileOpen((v) => !v)}
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
