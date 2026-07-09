import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Database, ShieldCheck, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useHealth } from "@/hooks/use-health";

const pillars = [
  {
    icon: BookOpen,
    title: "Your documents only",
    body: "Answers are grounded in retrieved chunks from your knowledge base — never invented.",
  },
  {
    icon: Database,
    title: "Hybrid knowledge",
    body: "Personal libraries plus optional organization workspaces with role-based access.",
  },
  {
    icon: ShieldCheck,
    title: "Citation-first",
    body: "Every response will show source document, page, chunk, and similarity score.",
  },
];

export function LandingPage() {
  const health = useHealth();

  return (
    <div className="space-y-12">
      <section className="relative overflow-hidden rounded-2xl border border-border/60 bg-card/60 p-8 shadow-sm md:p-12">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,hsl(166_70%_42%/0.15),transparent_45%)]" />
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="relative max-w-2xl space-y-5"
        >
          <Badge variant="secondary">Production-ready · Grounded RAG</Badge>
          <p className="font-display text-4xl font-extrabold tracking-tight text-foreground md:text-5xl">
            Knowledge Chatbot
          </p>
          <h1 className="text-xl text-muted-foreground md:text-2xl">
            Ask questions against your own documents — policies, papers, guidelines, and local data.
          </h1>
          <p className="text-sm text-muted-foreground">
            If the answer is not in your knowledge base, the assistant refuses instead of guessing.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Button asChild>
              <Link to="/signup">
                Get started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/login">Sign in</Link>
            </Button>
            <Button variant="ghost" asChild>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
                API docs
              </a>
            </Button>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            {health.isLoading && <span>Checking API…</span>}
            {health.isError && <span>API offline (start backend on :8000)</span>}
            {health.data && (
              <span>
                API {health.data.status} · v{health.data.version} · phase {health.data.phase}
              </span>
            )}
          </div>
        </motion.div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {pillars.map((pillar, index) => (
          <motion.article
            key={pillar.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index, duration: 0.35 }}
            className="rounded-xl border border-border/50 bg-card/40 p-5"
          >
            <pillar.icon className="mb-3 h-5 w-5 text-primary" />
            <h2 className="font-display text-lg font-semibold">{pillar.title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{pillar.body}</p>
          </motion.article>
        ))}
      </section>
    </div>
  );
}
