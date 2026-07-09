import {
  BookOpen,
  Building2,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Shield,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  shortcut?: string;
  adminOnly?: boolean;
};

export const mainNavItems: NavItem[] = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard, shortcut: "G D" },
  { label: "Chat", href: "/app/chat", icon: MessageSquare, shortcut: "G C" },
  { label: "Knowledge", href: "/app/knowledge", icon: BookOpen, shortcut: "G K" },
  { label: "Organizations", href: "/app/organizations", icon: Building2 },
  { label: "Search", href: "/app/search", icon: Search, shortcut: "G S" },
  { label: "Settings", href: "/app/settings", icon: Settings, shortcut: "G ," },
  { label: "Admin", href: "/app/admin", icon: Shield, adminOnly: true },
];

export const authNavItems = [
  { label: "Sign in", href: "/login" },
  { label: "Create account", href: "/signup" },
];
