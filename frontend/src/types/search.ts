export type SearchMode = "semantic" | "keyword" | "hybrid";

export type SearchFilters = {
  document_ids?: string[];
  scope?: "personal" | "organization" | "all";
  organization_id?: string;
};

export type SearchRequest = {
  query: string;
  mode?: SearchMode;
  top_k?: number;
  filters?: SearchFilters;
};

export type SearchResultItem = {
  chunk_id: string;
  document_id: string;
  title: string;
  content: string;
  page_number: number | null;
  chunk_index: number;
  score: number;
  semantic_score: number;
  keyword_score: number;
  scope: string;
  citation: string;
};

export type SearchResponse = {
  query: string;
  mode: SearchMode;
  results: SearchResultItem[];
  total_candidates: number;
  has_sufficient_context: boolean;
};
