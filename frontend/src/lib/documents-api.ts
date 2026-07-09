import { api } from "@/lib/api";
import type { Document, DocumentContentResponse, DocumentListResponse } from "@/types/documents";

export async function uploadDocuments(
  files: File[],
  onProgress?: (percent: number) => void,
  organizationId?: string,
): Promise<Document[]> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const { data } = await api.post<Document[]>("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    params: organizationId ? { organization_id: organizationId } : undefined,
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data;
}

export async function ingestUrl(
  url: string,
  title?: string,
  organizationId?: string,
): Promise<Document> {
  const { data } = await api.post<Document>("/documents/url", { url, title }, {
    params: organizationId ? { organization_id: organizationId } : undefined,
  });
  return data;
}

export async function fetchDocuments(
  page = 1,
  pageSize = 20,
  organizationId?: string,
): Promise<DocumentListResponse> {
  const { data } = await api.get<DocumentListResponse>("/documents", {
    params: {
      page,
      page_size: pageSize,
      ...(organizationId ? { organization_id: organizationId } : {}),
    },
  });
  return data;
}

export async function fetchDocument(documentId: string): Promise<Document> {
  const { data } = await api.get<Document>(`/documents/${documentId}`);
  return data;
}

export async function fetchDocumentContent(documentId: string): Promise<DocumentContentResponse> {
  const { data } = await api.get<DocumentContentResponse>(`/documents/${documentId}/content`);
  return data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/documents/${documentId}`);
}
