export type AdminUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string;
};

export type AdminUserListResponse = {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminDocument = {
  id: string;
  owner_id: string;
  title: string;
  original_filename: string;
  status: string;
  file_size_bytes: number;
  chunk_count: number;
  scope: string;
  created_at: string;
};

export type AdminDocumentListResponse = {
  items: AdminDocument[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminStorageSummary = {
  total_bytes: number;
  document_count: number;
  by_status: Record<string, number>;
};

export type AdminAuditLog = {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

export type AdminAuditLogListResponse = {
  items: AdminAuditLog[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminAnalyticsSummary = {
  days: number;
  total_events: number;
  by_type: Record<string, number>;
  llm_calls: number;
  llm_avg_latency_ms: number;
  llm_total_tokens: number;
};

export type AdminAnalyticsEvent = {
  id: string;
  user_id: string | null;
  event_type: string;
  name: string;
  duration_ms: number | null;
  token_count: number | null;
  status: string | null;
  meta: Record<string, unknown>;
  created_at: string;
};

export type AdminAnalyticsEventListResponse = {
  items: AdminAnalyticsEvent[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminSystemConfig = {
  app_name: string;
  app_env: string;
  default_llm_provider: string;
  default_embedding_provider: string;
  rag_top_k: number;
  rag_similarity_threshold: number;
};

export type ReadinessResponse = {
  status: string;
  checks: Array<{ name: string; status: string; latency_ms?: number; message?: string }>;
};
