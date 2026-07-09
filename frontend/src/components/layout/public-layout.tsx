import { Link, Outlet } from "react-router-dom";
import { motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/app/theme-provider";
import { Button } from "@/components/ui/button";
import { authNavItems } from "@/lib/navigation";

export function PublicLayout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-border/70 bg-background/70 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="font-display text-lg font-bold tracking-tight text-primary">
              Knowledge Chatbot
            </span>
            <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
              Phase 14
            </span>
          </Link>
          <div className="flex items-center gap-2">
            {authNavItems.map((item) => (
              <Button key={item.href} variant="ghost" size="sm" asChild>
                <Link to={item.href}>{item.label}</Link>
              </Button>
            ))}
            <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={toggleTheme}>
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>
      <motion.main
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="mx-auto max-w-6xl px-4 py-10"
      >
        <Outlet />
      </motion.main>
    </div>
  );
}
