export type DocumentStatus = "pending" | "processing" | "ready" | "failed" | "deleted";

export type Document = {
  id: string;
  title: string;
  original_filename: string;
  content_type: string | null;
  extension: string | null;
  file_size_bytes: number;
  content_hash: string;
  scope: string;
  status: DocumentStatus;
  version: number;
  page_count: number | null;
  chunk_count: number;
  source_url: string | null;
  error_message: string | null;
  processed_at: string | null;
  created_at: string;
  updated_at: string;
  meta: Record<string, unknown>;
};

export type DocumentListResponse = {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
};

export type DocumentContentResponse = {
  document_id: string;
  text: string;
  page_count: number | null;
  chunk_count: number;
};
