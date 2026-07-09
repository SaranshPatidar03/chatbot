import { Link, Outlet } from "react-router-dom";
import { motion } from "framer-motion";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen">
      <div className="relative hidden w-1/2 overflow-hidden bg-primary lg:flex lg:flex-col lg:justify-between lg:p-10">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,hsl(36_90%_55%/0.25),transparent_50%)]" />
        <div>
          <Link to="/" className="font-display text-2xl font-bold text-primary-foreground">
            Knowledge Chatbot
          </Link>
          <p className="mt-6 max-w-md text-primary-foreground/80">
            Grounded answers from your documents. No hallucinations — if it is not in your knowledge
            base, the assistant says so.
          </p>
        </div>
        <p className="text-sm text-primary-foreground/60">Hybrid personal + organization workspaces</p>
      </div>
      <motion.div
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.35 }}
        className="flex w-full flex-col justify-center px-6 py-12 lg:w-1/2 lg:px-16"
      >
        <div className="mx-auto w-full max-w-md">
          <Outlet />
        </div>
      </motion.div>
    </div>
  );
}
