import { useState } from "react";

import { UploadZone } from "@/features/knowledge/upload-zone";
import { DocumentList } from "@/features/knowledge/document-list";
import { useDocuments } from "@/hooks/use-documents";
import { useOrganizations } from "@/hooks/use-organizations";
import { Label } from "@/components/ui/label";

export function KnowledgePage() {
  const orgsQuery = useOrganizations();
  const [organizationId, setOrganizationId] = useState<string>("");
  const selectedOrgId = organizationId || undefined;
  const documentsQuery = useDocuments(1, selectedOrgId);

  const scopeLabel = selectedOrgId
    ? orgsQuery.data?.items.find((org) => org.id === selectedOrgId)?.name ?? "Organization"
    : "Personal";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Knowledge Base</h1>
        <p className="text-sm text-muted-foreground">
          Upload documents to build your searchable, grounded knowledge base.
        </p>
      </div>

      <div className="max-w-md space-y-2">
        <Label htmlFor="knowledge-scope">Library</Label>
        <select
          id="knowledge-scope"
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          value={organizationId}
          onChange={(e) => setOrganizationId(e.target.value)}
        >
          <option value="">Personal knowledge base</option>
          {orgsQuery.data?.items.map((org) => (
            <option key={org.id} value={org.id}>
              {org.name}
            </option>
          ))}
        </select>
      </div>

      <UploadZone organizationId={selectedOrgId} onUploaded={() => documentsQuery.refetch()} />

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold">{scopeLabel} documents</h2>
          {documentsQuery.data ? (
            <span className="text-xs text-muted-foreground">{documentsQuery.data.total} total</span>
          ) : null}
        </div>
        <DocumentList
          documents={documentsQuery.data?.items ?? []}
          loading={documentsQuery.isLoading}
        />
      </section>
    </div>
  );
}
