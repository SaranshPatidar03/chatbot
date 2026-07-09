import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createChat, deleteChat, fetchChats, fetchMessages } from "@/lib/chat-api";
import { queryKeys } from "@/lib/query-keys";

export function useChats() {
  return useQuery({
    queryKey: queryKeys.chats,
    queryFn: fetchChats,
  });
}

export function useChatMessages(chatId: string | undefined) {
  return useQuery({
    queryKey: chatId ? queryKeys.chatMessages(chatId) : ["chat-messages", "none"],
    queryFn: () => fetchMessages(chatId!),
    enabled: Boolean(chatId),
  });
}

export function useCreateChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => createChat(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chats });
    },
  });
}

export function useDeleteChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (chatId: string) => deleteChat(chatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chats });
    },
  });
}
