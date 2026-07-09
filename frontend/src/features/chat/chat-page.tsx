import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Archive,
  Copy,
  Download,
  Loader2,
  Menu,
  MessageSquare,
  Pencil,
  Pin,
  Plus,
  RefreshCw,
  Search,
  Send,
  Square,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";

import { MarkdownContent } from "@/components/chat/markdown-content";
import { DocumentViewerPanel } from "@/components/document-viewer/document-viewer-panel";
import { ChatListSkeleton } from "@/components/layout/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useChatMessages, useChats, useCreateChat, useDeleteChat, useUpdateChat } from "@/hooks/use-chats";
import { exportChat, importChat, regenerateChatMessage, streamChatMessage } from "@/lib/chat-api";
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [renamingChatId, setRenamingChatId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const streamAbortRef = useRef<AbortController | null>(null);

  const { data: chatsData, isLoading: chatsLoading } = useChats();
  const { data: messagesData, refetch: refetchMessages } = useChatMessages(chatId);
  const createChat = useCreateChat();
  const deleteChat = useDeleteChat();
  const updateChat = useUpdateChat();
  const importInputRef = useRef<HTMLInputElement>(null);

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

  async function handlePin(chatIdToPin: string, pinned: boolean) {
    await updateChat.mutateAsync({ chatId: chatIdToPin, is_pinned: !pinned });
  }

  async function handleArchive(chatIdToArchive: string) {
    await updateChat.mutateAsync({ chatId: chatIdToArchive, is_archived: true });
    if (chatId === chatIdToArchive) navigate("/app/chat");
  }

  async function handleDelete(chatIdToDelete: string) {
    await deleteChat.mutateAsync(chatIdToDelete);
    if (chatId === chatIdToDelete) navigate("/app/chat");
  }

  async function handleExport(currentChatId: string) {
    const blob = await exportChat(currentChatId);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `chat-${currentChatId}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleRename(chatIdToRename: string, title: string) {
    const trimmed = title.trim();
    if (!trimmed) return;
    await updateChat.mutateAsync({ chatId: chatIdToRename, title: trimmed });
    setRenamingChatId(null);
    setRenameDraft("");
  }

  function handleStopStreaming() {
    streamAbortRef.current?.abort();
    streamAbortRef.current = null;
    setStreaming(false);
    setStreamText("");
    setStreamCitations([]);
  }

  async function handleImportFile(file: File) {
    const chat = await importChat(file);
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
    const controller = new AbortController();
    streamAbortRef.current = controller;

    try {
      await streamChatMessage(
        chatId,
        content,
        {
          onStart: () => {
            void refetchMessages();
          },
          onCitations: setStreamCitations,
          onToken: (token) => setStreamText((prev) => prev + token),
        },
        controller.signal,
      );
      await refetchMessages();
    } finally {
      streamAbortRef.current = null;
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
    const controller = new AbortController();
    streamAbortRef.current = controller;
    try {
      await regenerateChatMessage(
        chatId,
        message.id,
        {
          onCitations: setStreamCitations,
          onToken: (token) => setStreamText((prev) => prev + token),
        },
        controller.signal,
      );
      await refetchMessages();
    } finally {
      streamAbortRef.current = null;
      setStreaming(false);
      setStreamText("");
      setStreamCitations([]);
    }
  }

  const sidebar = (
    <>
      <div className="flex items-center justify-between border-b border-border/60 p-3">
        <h2 className="text-sm font-semibold">Chats</h2>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="ghost"
            aria-label="Import chat"
            onClick={() => importInputRef.current?.click()}
          >
            <Upload className="h-4 w-4" />
          </Button>
          <input
            ref={importInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleImportFile(file);
              e.target.value = "";
            }}
          />
          <Button size="sm" variant="outline" onClick={handleNewChat} disabled={createChat.isPending}>
            <Plus className="h-4 w-4" />
            New
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="md:hidden"
            aria-label="Close chat sidebar"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
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
            <div
              key={chat.id}
              className={cn(
                "group flex items-center gap-1 rounded-lg px-2 py-1 text-sm transition-colors hover:bg-muted",
                chatId === chat.id && "bg-muted",
              )}
            >
              {renamingChatId === chat.id ? (
                <Input
                  autoFocus
                  className="h-8"
                  value={renameDraft}
                  onChange={(e) => setRenameDraft(e.target.value)}
                  onBlur={() => void handleRename(chat.id, renameDraft)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void handleRename(chat.id, renameDraft);
                    if (e.key === "Escape") {
                      setRenamingChatId(null);
                      setRenameDraft("");
                    }
                  }}
                />
              ) : (
                <Link
                  to={`/app/chat/${chat.id}`}
                  className="flex min-w-0 flex-1 items-center gap-2 px-1 py-1"
                  onClick={() => setSidebarOpen(false)}
                >
                  <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="truncate">{chat.title}</span>
                  {chat.is_pinned ? <Pin className="h-3 w-3 text-accent" /> : null}
                </Link>
              )}
              <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  aria-label="Rename chat"
                  onClick={() => {
                    setRenamingChatId(chat.id);
                    setRenameDraft(chat.title);
                  }}
                >
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  aria-label={chat.is_pinned ? "Unpin chat" : "Pin chat"}
                  onClick={() => void handlePin(chat.id, chat.is_pinned)}
                >
                  <Pin className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  aria-label="Archive chat"
                  onClick={() => void handleArchive(chat.id)}
                >
                  <Archive className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7 text-destructive"
                  aria-label="Delete chat"
                  onClick={() => void handleDelete(chat.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );

  return (
    <div className="relative flex h-[calc(100vh-7rem)] overflow-hidden rounded-xl border border-border/60 bg-card/30">
      {sidebarOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          aria-label="Close chat sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "z-40 flex w-72 flex-col border-r border-border/60 bg-card md:static md:flex",
          sidebarOpen ? "fixed inset-y-0 left-0 shadow-xl" : "hidden md:flex",
        )}
      >
        {sidebar}
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        {chatId ? (
          <>
            <div className="flex items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="md:hidden"
                  aria-label="Open chat sidebar"
                  onClick={() => setSidebarOpen(true)}
                >
                  <Menu className="h-4 w-4" />
                </Button>
                {renamingChatId === chatId ? (
                  <Input
                    autoFocus
                    className="h-9 max-w-md"
                    value={renameDraft}
                    onChange={(e) => setRenameDraft(e.target.value)}
                    onBlur={() => void handleRename(chatId, renameDraft)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") void handleRename(chatId, renameDraft);
                      if (e.key === "Escape") {
                        setRenamingChatId(null);
                        setRenameDraft("");
                      }
                    }}
                  />
                ) : (
                  <h2 className="truncate font-medium">{activeChat?.title ?? "Chat"}</h2>
                )}
                {renamingChatId !== chatId ? (
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 shrink-0"
                    aria-label="Rename chat"
                    onClick={() => {
                      setRenamingChatId(chatId);
                      setRenameDraft(activeChat?.title ?? "Chat");
                    }}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                ) : null}
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void handleExport(chatId)}
              >
                <Download className="mr-1 h-4 w-4" />
                Export
              </Button>
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
                  {streaming ? (
                    <Button type="button" variant="outline" onClick={handleStopStreaming} aria-label="Stop generating">
                      <Square className="h-4 w-4" />
                    </Button>
                  ) : (
                    <Button type="submit" disabled={!draft.trim()}>
                      <Send className="h-4 w-4" />
                    </Button>
                  )}
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
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className={cn("max-w-2xl", isUser ? "ml-auto" : "")}>
      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm",
          isUser ? "bg-muted" : "border border-border/60 bg-card",
        )}
      >
        <MarkdownContent content={message.content} plain={isUser} />
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
        {!isUser && !streaming ? (
          <div className="mt-2 flex gap-1">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-8 px-2 text-xs"
              onClick={() => void handleCopy()}
            >
              <Copy className="mr-1 h-3 w-3" />
              {copied ? "Copied" : "Copy"}
            </Button>
            {onRegenerate ? (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-xs"
                onClick={onRegenerate}
                disabled={!canRegenerate}
              >
                <RefreshCw className="mr-1 h-3 w-3" />
                Regenerate
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
