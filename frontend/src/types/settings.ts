export type LlmProvider = "openai" | "ollama";

export type UserSettings = {
  theme: string;
  language: string;
  llm_provider: LlmProvider;
  llm_model: string;
  embedding_provider: LlmProvider;
  embedding_model: string;
  temperature: number;
  top_p: number;
  top_k: number;
  max_tokens: number;
  system_prompt: string | null;
  allow_general_knowledge: boolean;
  similarity_threshold: number;
  mmr_lambda: number;
  updated_at: string;
};

export type UserSettingsUpdate = Partial<
  Pick<
    UserSettings,
    | "theme"
    | "language"
    | "llm_provider"
    | "llm_model"
    | "embedding_provider"
    | "embedding_model"
    | "temperature"
    | "top_p"
    | "top_k"
    | "max_tokens"
    | "system_prompt"
    | "allow_general_knowledge"
    | "similarity_threshold"
    | "mmr_lambda"
  >
>;
