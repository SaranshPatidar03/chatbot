import { X } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDocumentContent } from "@/lib/documents-api";
import type { Citation } from "@/types/chat";

type DocumentViewerPanelProps = {
  citation: Citation | null;
  onClose: () => void;
};

export function DocumentViewerPanel({ citation, onClose }: DocumentViewerPanelProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!citation) return;
    setLoading(true);
    setError(null);
    fetchDocumentContent(citation.document_id)
      .then((response) => setText(response.text))
      .catch(() => setError("Could not load document content."))
      .finally(() => setLoading(false));
  }, [citation]);

  if (!citation) return null;

  const highlight = citation.content_preview?.trim();

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full max-w-md border-l border-border/60 bg-background p-4 shadow-xl">
      <Card className="h-full border-0 shadow-none">
        <CardHeader className="px-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <CardTitle className="text-base">{citation.title}</CardTitle>
              <CardDescription>{citation.citation}</CardDescription>
            </div>
            <Button size="icon" variant="ghost" onClick={onClose} aria-label="Close viewer">
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            <Badge variant="muted">score {citation.score.toFixed(3)}</Badge>
            {citation.page_number ? <Badge variant="outline">page {citation.page_number}</Badge> : null}
          </div>
        </CardHeader>
        <CardContent className="h-[calc(100%-7rem)] overflow-y-auto px-0">
          {loading ? <p className="text-sm text-muted-foreground">Loading document…</p> : null}
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {!loading && !error ? (
            <pre className="whitespace-pre-wrap rounded-lg bg-muted/50 p-4 text-sm leading-relaxed">
              {highlight && text.includes(highlight) ? (
                text.split(highlight).map((part, index, array) => (
                  <span key={`${index}-${part.slice(0, 12)}`}>
                    {part}
                    {index < array.length - 1 ? (
                      <mark className="rounded bg-accent/30 px-0.5">{highlight}</mark>
                    ) : null}
                  </span>
                ))
              ) : (
                text
              )}
            </pre>
          ) : null}
          <Button variant="outline" className="mt-4" asChild>
            <a href={`/api/v1/documents/${citation.document_id}/file`} target="_blank" rel="noreferrer">
              Open original file
            </a>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
