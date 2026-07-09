import { getAccessToken } from "@/lib/auth-storage";
import type { Chat, ChatListResponse, Citation, MessageListResponse, StreamHandlers } from "@/types/chat";

const rawBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
const apiBase = rawBase ?? "/api/v1";

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function fetchChats(): Promise<ChatListResponse> {
  const response = await fetch(`${apiBase}/chats`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Failed to load chats");
  return response.json();
}

export async function createChat(title?: string): Promise<Chat> {
  const response = await fetch(`${apiBase}/chats`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ title }),
  });
  if (!response.ok) throw new Error("Failed to create chat");
  return response.json();
}

export async function deleteChat(chatId: string): Promise<void> {
  const response = await fetch(`${apiBase}/chats/${chatId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error("Failed to delete chat");
}

export async function fetchMessages(chatId: string): Promise<MessageListResponse> {
  const response = await fetch(`${apiBase}/chats/${chatId}/messages`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Failed to load messages");
  return response.json();
}

async function consumeSseStream(response: Response, handlers: StreamHandlers): Promise<void> {
  if (!response.ok || !response.body) {
    handlers.onError?.("Streaming request failed.");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      let dataLine = "";
      for (const line of lines) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        if (line.startsWith("data:")) dataLine = line.slice(5).trim();
      }
      if (!dataLine) continue;
      const data = JSON.parse(dataLine) as Record<string, unknown>;

      if (eventName === "start") handlers.onStart?.(data as { user_message_id: string });
      if (eventName === "citations") handlers.onCitations?.((data.citations ?? []) as Citation[]);
      if (eventName === "token") handlers.onToken?.(String(data.content ?? ""));
      if (eventName === "done") handlers.onDone?.(data as { message_id: string; latency_ms: number });
    }
  }
}

export async function streamChatMessage(
  chatId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${apiBase}/chats/${chatId}/messages`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ content }),
    signal,
  });
  await consumeSseStream(response, handlers);
}

export async function regenerateChatMessage(
  chatId: string,
  messageId: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${apiBase}/chats/${chatId}/messages/${messageId}/regenerate`, {
    method: "POST",
    headers: authHeaders(),
    signal,
  });
  await consumeSseStream(response, handlers);
}
