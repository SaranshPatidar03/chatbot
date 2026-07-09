import { Link, useNavigate, useParams } from "react-router-dom";
import { Loader2, MessageSquare, Pin, Plus, RefreshCw, Search, Send } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { DocumentViewerPanel } from "@/components/document-viewer/document-viewer-panel";
import { ChatListSkeleton } from "@/components/layout/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useChatMessages, useChats, useCreateChat } from "@/hooks/use-chats";
import { regenerateChatMessage, streamChatMessage } from "@/lib/chat-api";
import { cn } from "@/lib/utils";
import type { ChatMessage, Citation } from "@/types/chat";

export function ChatPage() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [streamCitations, setStreamCitations] = useState<Citation[]>([]);
  const [viewerCitation, setViewerCitation] = useState<Citation | null>(null);

  const { data: chatsData, isLoading: chatsLoading } = useChats();
  const { data: messagesData, refetch: refetchMessages } = useChatMessages(chatId);
  const createChat = useCreateChat();

  const filtered = useMemo(() => {
    const items = chatsData?.items ?? [];
    if (!query.trim()) return items;
    return items.filter((chat) => chat.title.toLowerCase().includes(query.toLowerCase()));
  }, [chatsData, query]);

  const messages = messagesData?.items ?? [];
  const activeChat = chatsData?.items.find((chat) => chat.id === chatId);

  async function handleNewChat() {
    const chat = await createChat.mutateAsync(undefined);
    navigate(`/app/chat/${chat.id}`);
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!chatId || !draft.trim() || streaming) return;

    const content = draft.trim();
    setDraft("");
    setStreaming(true);
    setStreamText("");
    setStreamCitations([]);

    try {
      await streamChatMessage(chatId, content, {
        onStart: () => {
          void refetchMessages();
        },
        onCitations: setStreamCitations,
        onToken: (token) => setStreamText((prev) => prev + token),
      });
      await refetchMessages();
    } finally {
      setStreaming(false);
      setStreamText("");
      setStreamCitations([]);
    }
  }

  async function handleRegenerate(message: ChatMessage) {
    if (!chatId || streaming || message.role !== "assistant") return;
    setStreaming(true);
    setStreamText("");
    setStreamCitations([]);
    try {
      await regenerateChatMessage(chatId, message.id, {
        onCitations: setStreamCitations,
        onToken: (token) => setStreamText((prev) => prev + token),
      });
      await refetchMessages();
    } finally {
      setStreaming(false);
      setStreamText("");
      setStreamCitations([]);
    }
  }

  return (
    <div className="relative flex h-[calc(100vh-7rem)] overflow-hidden rounded-xl border border-border/60 bg-card/30">
      <aside className="hidden w-72 flex-col border-r border-border/60 md:flex">
        <div className="flex items-center justify-between border-b border-border/60 p-3">
          <h2 className="text-sm font-semibold">Chats</h2>
          <Button size="sm" variant="outline" onClick={handleNewChat} disabled={createChat.isPending}>
            <Plus className="h-4 w-4" />
            New
          </Button>
        </div>
        <div className="p-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-8"
              placeholder="Search chats"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
        {chatsLoading ? (
          <ChatListSkeleton />
        ) : (
          <div className="flex-1 space-y-1 overflow-y-auto p-2">
            {filtered.map((chat) => (
              <Link
                key={chat.id}
                to={`/app/chat/${chat.id}`}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted",
                  chatId === chat.id && "bg-muted text-foreground",
                )}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate">{chat.title}</span>
                {chat.is_pinned ? <Pin className="h-3 w-3 text-accent" /> : null}
              </Link>
            ))}
          </div>
        )}
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        {chatId ? (
          <>
            <div className="border-b border-border/60 px-4 py-3">
              <h2 className="font-medium">{activeChat?.title ?? "Chat"}</h2>
            </div>
            <div className="flex-1 space-y-4 overflow-y-auto p-4">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onCitationClick={setViewerCitation}
                  onRegenerate={() => handleRegenerate(message)}
                  canRegenerate={!streaming}
                />
              ))}
              {streaming ? (
                <MessageBubble
                  message={{
                    id: "streaming",
                    chat_id: chatId,
                    role: "assistant",
                    content: streamText || "…",
                    citations: streamCitations,
                    latency_ms: null,
                    model_provider: null,
                    model_name: null,
                    created_at: new Date().toISOString(),
                  }}
                  onCitationClick={setViewerCitation}
                  streaming
                />
              ) : null}
            </div>
            <div className="border-t border-border/60 p-4">
              <form onSubmit={handleSend}>
                <Card className="flex items-center gap-2 p-2">
                  <Input
                    placeholder="Ask a question about your documents…"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    disabled={streaming}
                  />
                  <Button type="submit" disabled={streaming || !draft.trim()}>
                    {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </Card>
              </form>
            </div>
          </>
        ) : (
          <EmptyChatState onCreate={handleNewChat} creating={createChat.isPending} />
        )}
      </section>

      <DocumentViewerPanel citation={viewerCitation} onClose={() => setViewerCitation(null)} />
    </div>
  );
}

function EmptyChatState({ onCreate, creating }: { onCreate: () => void; creating: boolean }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="rounded-full bg-primary/10 p-4 text-primary">
        <MessageSquare className="h-8 w-8" />
      </div>
      <div>
        <h2 className="font-display text-xl font-semibold">Start a grounded conversation</h2>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          Ask questions grounded in your uploaded knowledge. Answers stream with citations you can inspect.
        </p>
      </div>
      <Button onClick={onCreate} disabled={creating}>
        {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        New chat
      </Button>
    </div>
  );
}

function MessageBubble({
  message,
  onCitationClick,
  onRegenerate,
  canRegenerate = false,
  streaming = false,
}: {
  message: ChatMessage;
  onCitationClick: (citation: Citation) => void;
  onRegenerate?: () => void;
  canRegenerate?: boolean;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <div className={cn("max-w-2xl", isUser ? "ml-auto" : "")}>
      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm",
          isUser ? "bg-muted" : "border border-border/60 bg-card",
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && message.citations.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.citations.map((citation) => (
              <button key={citation.chunk_id} type="button" onClick={() => onCitationClick(citation)}>
                <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80">
                  {citation.citation}
                </Badge>
              </button>
            ))}
          </div>
        ) : null}
        {!isUser && !streaming && onRegenerate ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="mt-2 h-8 px-2 text-xs"
            onClick={onRegenerate}
            disabled={!canRegenerate}
          >
            <RefreshCw className="mr-1 h-3 w-3" />
            Regenerate
          </Button>
        ) : null}
      </div>
    </div>
  );
}
