import { api } from "@/lib/api";

export type DashboardSummary = {
  document_count: number;
  chat_count: number;
  storage_bytes: number;
  documents_processing: number;
  recent_documents: Array<{
    id: string;
    title: string;
    status: string;
    file_size_bytes: number;
    created_at: string;
  }>;
  recent_chats: Array<{
    id: string;
    title: string;
    updated_at: string;
  }>;
};

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/dashboard/summary");
  return data;
}
