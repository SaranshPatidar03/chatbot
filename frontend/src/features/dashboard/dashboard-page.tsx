import { Link } from "react-router-dom";
import { FileText, HardDrive, MessageSquare, Sparkles } from "lucide-react";

import { DashboardStatsSkeleton } from "@/components/layout/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardSummary } from "@/hooks/use-dashboard";
import { useHealth } from "@/hooks/use-health";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export function DashboardPage() {
  const health = useHealth();
  const summary = useDashboardSummary();
  const loading = health.isLoading || summary.isLoading;
  const data = summary.data;

  const embeddingStatus =
    data && data.documents_processing > 0
      ? `${data.documents_processing} processing`
      : "Idle";

  const stats = [
    {
      label: "Documents",
      value: data ? String(data.document_count) : "—",
      hint: "Personal and org libraries",
      icon: FileText,
    },
    {
      label: "Chats",
      value: data ? String(data.chat_count) : "—",
      hint: "Grounded conversations",
      icon: MessageSquare,
    },
    {
      label: "Storage used",
      value: data ? formatBytes(data.storage_bytes) : "—",
      hint: "Uploaded file bytes",
      icon: HardDrive,
    },
    {
      label: "Embedding status",
      value: embeddingStatus,
      hint: "Background indexing workers",
      icon: Sparkles,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Overview of your knowledge base and recent activity.
          </p>
        </div>
        {health.data ? (
          <Badge variant="muted">API phase {health.data.phase}</Badge>
        ) : null}
      </div>

      {loading ? (
        <DashboardStatsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>{stat.label}</CardDescription>
                  <stat.icon className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="text-3xl">{stat.value}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{stat.hint}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent uploads</CardTitle>
            <CardDescription>Latest documents in your libraries.</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : data && data.recent_documents.length > 0 ? (
              <ul className="space-y-2 text-sm">
                {data.recent_documents.map((doc) => (
                  <li key={doc.id} className="flex items-center justify-between gap-2">
                    <Link
                      to="/app/knowledge"
                      className="truncate font-medium text-primary hover:underline"
                    >
                      {doc.title}
                    </Link>
                    <span className="shrink-0 text-xs text-muted-foreground">{doc.status}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                No uploads yet.{" "}
                <Link to="/app/knowledge" className="text-primary hover:underline">
                  Add documents
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent chats</CardTitle>
            <CardDescription>Your latest grounded conversations.</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : data && data.recent_chats.length > 0 ? (
              <ul className="space-y-2 text-sm">
                {data.recent_chats.map((chat) => (
                  <li key={chat.id} className="flex items-center justify-between gap-2">
                    <Link
                      to={`/app/chat?chat=${chat.id}`}
                      className="truncate font-medium text-primary hover:underline"
                    >
                      {chat.title}
                    </Link>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {formatDate(chat.updated_at)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                No conversations yet.{" "}
                <Link to="/app/chat" className="text-primary hover:underline">
                  Start chatting
                </Link>
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
