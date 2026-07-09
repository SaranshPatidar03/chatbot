import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Database, FileText, Users } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  deleteAdminDocument,
  fetchAdminAnalyticsEvents,
  fetchAdminAnalyticsSummary,
  fetchAdminAuditLogs,
  fetchAdminDocuments,
  fetchAdminStorageSummary,
  fetchAdminSystemConfig,
  fetchAdminSystemHealth,
  fetchAdminUsers,
  formatBytes,
  updateAdminUser,
} from "@/lib/admin-api";

const tabs = [
  { id: "users", label: "Users", icon: Users },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "analytics", label: "Analytics", icon: Activity },
  { id: "system", label: "System", icon: Database },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function AdminPage() {
  const [tab, setTab] = useState<TabId>("users");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Admin</h1>
          <p className="text-sm text-muted-foreground">
            Platform administration for users, storage, analytics, and system health.
          </p>
        </div>
        <Badge>Platform admin</Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((item) => (
          <Button
            key={item.id}
            size="sm"
            variant={tab === item.id ? "default" : "outline"}
            onClick={() => setTab(item.id)}
          >
            <item.icon className="mr-2 h-4 w-4" />
            {item.label}
          </Button>
        ))}
      </div>

      {tab === "users" ? <UsersPanel /> : null}
      {tab === "documents" ? <DocumentsPanel /> : null}
      {tab === "analytics" ? <AnalyticsPanel /> : null}
      {tab === "system" ? <SystemPanel /> : null}
    </div>
  );
}

function UsersPanel() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin", "users"], queryFn: () => fetchAdminUsers() });
  const mutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateAdminUser(userId, { role }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });

  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (error) return <p className="text-sm text-destructive">Failed to load users.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
        <CardDescription>{data?.total ?? 0} accounts</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {data?.items.map((user) => (
          <div key={user.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm">
            <div>
              <p className="font-medium">{user.email}</p>
              <p className="text-muted-foreground">{user.full_name ?? "—"}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={user.role === "platform_admin" ? "secondary" : "outline"}>{user.role}</Badge>
              <Badge variant={user.is_active ? "muted" : "outline"}>
                {user.is_active ? "active" : "inactive"}
              </Badge>
              {user.role !== "platform_admin" ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => mutation.mutate({ userId: user.id, role: "platform_admin" })}
                >
                  Promote
                </Button>
              ) : null}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DocumentsPanel() {
  const queryClient = useQueryClient();
  const storage = useQuery({ queryKey: ["admin", "storage"], queryFn: fetchAdminStorageSummary });
  const docs = useQuery({ queryKey: ["admin", "documents"], queryFn: () => fetchAdminDocuments() });
  const deleteMutation = useMutation({
    mutationFn: deleteAdminDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "documents"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "storage"] });
    },
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total storage</CardDescription>
            <CardTitle>{formatBytes(storage.data?.total_bytes ?? 0)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Documents</CardDescription>
            <CardTitle>{storage.data?.document_count ?? 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Ready</CardDescription>
            <CardTitle>{storage.data?.by_status.ready ?? 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {docs.isLoading ? <Skeleton className="h-24 w-full" /> : null}
          {docs.data?.items.map((doc) => (
            <div key={doc.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm">
              <div>
                <p className="font-medium">{doc.title}</p>
                <p className="text-muted-foreground">
                  {doc.status} · {formatBytes(doc.file_size_bytes)} · {doc.chunk_count} chunks
                </p>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => deleteMutation.mutate(doc.id)}
                disabled={deleteMutation.isPending}
              >
                Delete
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function AnalyticsPanel() {
  const summary = useQuery({ queryKey: ["admin", "analytics", "summary"], queryFn: () => fetchAdminAnalyticsSummary() });
  const events = useQuery({ queryKey: ["admin", "analytics", "events"], queryFn: () => fetchAdminAnalyticsEvents() });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Events (7d)" value={summary.data?.total_events ?? 0} />
        <MetricCard label="LLM calls" value={summary.data?.llm_calls ?? 0} />
        <MetricCard label="Avg LLM latency" value={`${summary.data?.llm_avg_latency_ms ?? 0} ms`} />
        <MetricCard label="LLM tokens" value={summary.data?.llm_total_tokens ?? 0} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent events</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {events.data?.items.slice(0, 20).map((event) => (
            <div key={event.id} className="flex flex-wrap justify-between gap-2 rounded border p-2 text-xs">
              <span className="font-medium">{event.name}</span>
              <span className="text-muted-foreground">{event.event_type}</span>
              <span className="text-muted-foreground">{event.status ?? "—"}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function SystemPanel() {
  const health = useQuery({ queryKey: ["admin", "system", "health"], queryFn: fetchAdminSystemHealth });
  const config = useQuery({ queryKey: ["admin", "system", "config"], queryFn: fetchAdminSystemConfig });
  const audit = useQuery({ queryKey: ["admin", "audit"], queryFn: () => fetchAdminAuditLogs() });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Dependencies</CardTitle>
          <CardDescription>Extended readiness checks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {health.data?.checks.map((check) => (
            <div key={check.name} className="flex items-center justify-between rounded border p-2 text-sm">
              <span>{check.name}</span>
              <Badge variant={check.status === "ok" ? "secondary" : "outline"}>{check.status}</Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Row label="Environment" value={config.data?.app_env ?? "—"} />
          <Row label="LLM provider" value={config.data?.default_llm_provider ?? "—"} />
          <Row label="Embedding provider" value={config.data?.default_embedding_provider ?? "—"} />
          <Row label="RAG top K" value={String(config.data?.rag_top_k ?? "—")} />
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Audit logs</CardTitle>
          <CardDescription>{audit.data?.total ?? 0} entries</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {audit.data?.items.slice(0, 15).map((log) => (
            <div key={log.id} className="rounded border p-2 text-xs">
              <span className="font-medium">{log.action}</span>
              <span className="ml-2 text-muted-foreground">{log.resource_type ?? "—"}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle>{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
