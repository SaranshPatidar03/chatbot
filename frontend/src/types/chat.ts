export type Citation = {
  chunk_id: string;
  document_id: string;
  title: string;
  content_preview: string;
  page_number: number | null;
  chunk_index: number;
  score: number;
  citation: string;
};

export type Chat = {
  id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  organization_id: string | null;
  model_provider: string | null;
  model_name: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatListResponse = {
  items: Chat[];
  total: number;
};

export type ChatMessage = {
  id: string;
  chat_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  latency_ms: number | null;
  model_provider: string | null;
  model_name: string | null;
  created_at: string;
};

export type MessageListResponse = {
  items: ChatMessage[];
  total: number;
};

export type StreamHandlers = {
  onStart?: (payload: { user_message_id: string }) => void;
  onCitations?: (citations: Citation[]) => void;
  onToken?: (content: string) => void;
  onDone?: (payload: { message_id: string; latency_ms: number }) => void;
  onError?: (message: string) => void;
};
