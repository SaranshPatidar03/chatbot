import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  fetchDocuments,
  ingestUrl,
  uploadDocuments,
} from "@/lib/documents-api";
import { queryKeys } from "@/lib/query-keys";

export function useDocuments(page = 1, organizationId?: string) {
  return useQuery({
    queryKey: [...queryKeys.documents, organizationId ?? "personal", page],
    queryFn: () => fetchDocuments(page, 20, organizationId),
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const processing = items.some((doc) => doc.status === "pending" || doc.status === "processing");
      return processing ? 3000 : false;
    },
  });
}

export function useUploadDocuments(organizationId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ files, onProgress }: { files: File[]; onProgress?: (n: number) => void }) =>
      uploadDocuments(files, onProgress, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

export function useIngestUrl(organizationId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ url, title }: { url: string; title?: string }) =>
      ingestUrl(url, title, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}
