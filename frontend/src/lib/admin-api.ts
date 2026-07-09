import { api } from "@/lib/api";
import type {
  AdminAnalyticsEventListResponse,
  AdminAnalyticsSummary,
  AdminAuditLogListResponse,
  AdminDocumentListResponse,
  AdminStorageSummary,
  AdminSystemConfig,
  AdminUserListResponse,
  ReadinessResponse,
} from "@/types/admin";

export async function fetchAdminUsers(page = 1): Promise<AdminUserListResponse> {
  const { data } = await api.get<AdminUserListResponse>("/admin/users", { params: { page } });
  return data;
}

export async function updateAdminUser(
  userId: string,
  payload: { role?: string; is_active?: boolean; is_verified?: boolean },
): Promise<void> {
  await api.patch(`/admin/users/${userId}`, payload);
}

export async function fetchAdminDocuments(page = 1): Promise<AdminDocumentListResponse> {
  const { data } = await api.get<AdminDocumentListResponse>("/admin/documents", { params: { page } });
  return data;
}

export async function fetchAdminStorageSummary(): Promise<AdminStorageSummary> {
  const { data } = await api.get<AdminStorageSummary>("/admin/storage/summary");
  return data;
}

export async function deleteAdminDocument(documentId: string): Promise<void> {
  await api.delete(`/admin/documents/${documentId}`);
}

export async function fetchAdminAuditLogs(page = 1): Promise<AdminAuditLogListResponse> {
  const { data } = await api.get<AdminAuditLogListResponse>("/admin/audit-logs", { params: { page } });
  return data;
}

export async function fetchAdminAnalyticsSummary(days = 7): Promise<AdminAnalyticsSummary> {
  const { data } = await api.get<AdminAnalyticsSummary>("/admin/analytics/summary", { params: { days } });
  return data;
}

export async function fetchAdminAnalyticsEvents(page = 1): Promise<AdminAnalyticsEventListResponse> {
  const { data } = await api.get<AdminAnalyticsEventListResponse>("/admin/analytics/events", {
    params: { page },
  });
  return data;
}

export async function fetchAdminSystemHealth(): Promise<ReadinessResponse> {
  const { data } = await api.get<ReadinessResponse>("/admin/system/health");
  return data;
}

export async function fetchAdminSystemConfig(): Promise<AdminSystemConfig> {
  const { data } = await api.get<AdminSystemConfig>("/admin/system/config");
  return data;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export { formatBytes };
