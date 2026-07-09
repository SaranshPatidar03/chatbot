import { api } from "@/lib/api";
import type { SearchRequest, SearchResponse } from "@/types/search";

export async function searchKnowledge(payload: SearchRequest): Promise<SearchResponse> {
  const { data } = await api.post<SearchResponse>("/search", payload);
  return data;
}
