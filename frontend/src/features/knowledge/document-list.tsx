import { FileText, Loader2, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeleteDocument } from "@/hooks/use-documents";
import type { Document } from "@/types/documents";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusVariant(status: Document["status"]) {
  switch (status) {
    case "ready":
      return "default" as const;
    case "failed":
      return "outline" as const;
    case "processing":
    case "pending":
      return "secondary" as const;
    default:
      return "muted" as const;
  }
}

type DocumentListProps = {
  documents: Document[];
  loading?: boolean;
};

export function DocumentList({ documents, loading }: DocumentListProps) {
  const deleteDocument = useDeleteDocument();

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-20 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!documents.length) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
          <FileText className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No documents yet. Upload files to get started.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((document) => (
        <Card key={document.id}>
          <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 pb-2">
            <div className="min-w-0">
              <CardTitle className="truncate text-base">{document.title}</CardTitle>
              <CardDescription className="truncate">
                {document.original_filename} · {formatBytes(document.file_size_bytes)} · v{document.version}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={statusVariant(document.status)}>
                {document.status === "processing" || document.status === "pending" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : null}
                {document.status}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Delete document"
                onClick={() => deleteDocument.mutate(document.id)}
                disabled={deleteDocument.isPending}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            {document.chunk_count} chunks
            {document.page_count ? ` · ${document.page_count} pages` : ""}
            {document.error_message ? ` · ${document.error_message}` : ""}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
