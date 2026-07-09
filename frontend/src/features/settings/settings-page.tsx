import { FormEvent, useEffect, useState } from "react";

import { useAuthContext } from "@/app/auth-provider";
import { useTheme } from "@/app/theme-provider";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useUpdateUserSettings, useUserSettings } from "@/hooks/use-user-settings";
import { updateProfileRequest } from "@/lib/auth-api";
import { persistAuth, getAccessToken, getRefreshToken } from "@/lib/auth-storage";
import type { LlmProvider } from "@/types/settings";

const DEFAULT_SYSTEM_PROMPT =
  "You are an AI assistant.\nAnswer ONLY using retrieved context.\nNever fabricate information.";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user, refetchUser } = useAuthContext();
  const settingsQuery = useUserSettings();
  const updateSettings = useUpdateUserSettings();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? "");
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [llmProvider, setLlmProvider] = useState<LlmProvider>("ollama");
  const [llmModel, setLlmModel] = useState("llama3");
  const [embeddingProvider, setEmbeddingProvider] = useState<LlmProvider>("ollama");
  const [embeddingModel, setEmbeddingModel] = useState("nomic-embed-text");
  const [temperature, setTemperature] = useState("0.2");
  const [topP, setTopP] = useState("1");
  const [topK, setTopK] = useState("8");
  const [maxTokens, setMaxTokens] = useState("1024");
  const [similarityThreshold, setSimilarityThreshold] = useState("0.35");
  const [mmrLambda, setMmrLambda] = useState("0.5");
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [allowGeneralKnowledge, setAllowGeneralKnowledge] = useState(false);
  const [modelsMessage, setModelsMessage] = useState<string | null>(null);
  const [modelsError, setModelsError] = useState<string | null>(null);

  useEffect(() => {
    setFullName(user?.full_name ?? "");
    setAvatarUrl(user?.avatar_url ?? "");
  }, [user]);

  useEffect(() => {
    if (!settingsQuery.data) return;
    const settings = settingsQuery.data;
    setLlmProvider(settings.llm_provider);
    setLlmModel(settings.llm_model);
    setEmbeddingProvider(settings.embedding_provider);
    setEmbeddingModel(settings.embedding_model);
    setTemperature(String(settings.temperature));
    setTopP(String(settings.top_p));
    setTopK(String(settings.top_k));
    setMaxTokens(String(settings.max_tokens));
    setSimilarityThreshold(String(settings.similarity_threshold));
    setMmrLambda(String(settings.mmr_lambda));
    setSystemPrompt(settings.system_prompt ?? DEFAULT_SYSTEM_PROMPT);
    setAllowGeneralKnowledge(settings.allow_general_knowledge);
  }, [settingsQuery.data]);

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault();
    setProfileMessage(null);
    setProfileError(null);
    setSavingProfile(true);
    try {
      const updated = await updateProfileRequest({
        full_name: fullName.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      });
      const access = getAccessToken();
      const refresh = getRefreshToken();
      if (access && refresh) {
        persistAuth(access, refresh, updated);
      }
      await refetchUser();
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Unable to update profile.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function onThemeChange(value: "light" | "dark") {
    setTheme(value);
    try {
      await updateSettings.mutateAsync({ theme: value });
    } catch {
      // Theme still applies locally if the API call fails.
    }
  }

  async function onSaveModels(event: FormEvent) {
    event.preventDefault();
    setModelsMessage(null);
    setModelsError(null);
    try {
      await updateSettings.mutateAsync({
        llm_provider: llmProvider,
        llm_model: llmModel.trim(),
        embedding_provider: embeddingProvider,
        embedding_model: embeddingModel.trim(),
        temperature: Number(temperature),
        top_p: Number(topP),
        top_k: Number(topK),
        max_tokens: Number(maxTokens),
        similarity_threshold: Number(similarityThreshold),
        mmr_lambda: Number(mmrLambda),
        system_prompt: systemPrompt.trim() || null,
        allow_general_knowledge: allowGeneralKnowledge,
      });
      setModelsMessage("Model and RAG settings saved.");
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : "Unable to save settings.");
    }
  }

  const settingsLoading = settingsQuery.isLoading;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Profile, theme, models, and RAG parameters for your assistant.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your account details.</CardDescription>
        </CardHeader>
        <CardContent>
          {profileMessage ? <Alert variant="success" className="mb-4">{profileMessage}</Alert> : null}
          {profileError ? <Alert variant="destructive" className="mb-4">{profileError}</Alert> : null}
          <form onSubmit={onSaveProfile} className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={user?.email ?? ""} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Full name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="avatarUrl">Avatar URL</Label>
              <Input
                id="avatarUrl"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://..."
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={savingProfile}>
                {savingProfile ? "Saving…" : "Save profile"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Theme preference syncs to your account.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {(["light", "dark"] as const).map((value) => (
            <Button
              key={value}
              variant={theme === value ? "default" : "outline"}
              onClick={() => onThemeChange(value)}
            >
              {value}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Models</CardTitle>
          <CardDescription>LLM and embedding provider preferences for chat and indexing.</CardDescription>
        </CardHeader>
        <CardContent>
          {modelsMessage ? <Alert variant="success" className="mb-4">{modelsMessage}</Alert> : null}
          {modelsError ? <Alert variant="destructive" className="mb-4">{modelsError}</Alert> : null}
          <form onSubmit={onSaveModels} className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="llmProvider">LLM provider</Label>
              <select
                id="llmProvider"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={llmProvider}
                disabled={settingsLoading}
                onChange={(e) => setLlmProvider(e.target.value as LlmProvider)}
              >
                <option value="ollama">ollama</option>
                <option value="openai">openai</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="llmModel">LLM model</Label>
              <Input
                id="llmModel"
                value={llmModel}
                disabled={settingsLoading}
                onChange={(e) => setLlmModel(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="embeddingProvider">Embedding provider</Label>
              <select
                id="embeddingProvider"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={embeddingProvider}
                disabled={settingsLoading}
                onChange={(e) => setEmbeddingProvider(e.target.value as LlmProvider)}
              >
                <option value="ollama">ollama</option>
                <option value="openai">openai</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="embeddingModel">Embedding model</Label>
              <Input
                id="embeddingModel"
                value={embeddingModel}
                disabled={settingsLoading}
                onChange={(e) => setEmbeddingModel(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={settingsLoading || updateSettings.isPending}>
                {updateSettings.isPending ? "Saving…" : "Save model settings"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>RAG parameters</CardTitle>
          <CardDescription>Temperature, retrieval, and generation limits.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSaveModels} className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="temperature">Temperature</Label>
              <Input
                id="temperature"
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={temperature}
                disabled={settingsLoading}
                onChange={(e) => setTemperature(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="topK">Top K retrieval</Label>
              <Input
                id="topK"
                type="number"
                min="1"
                max="50"
                value={topK}
                disabled={settingsLoading}
                onChange={(e) => setTopK(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxTokens">Max tokens</Label>
              <Input
                id="maxTokens"
                type="number"
                min="64"
                max="8192"
                value={maxTokens}
                disabled={settingsLoading}
                onChange={(e) => setMaxTokens(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="similarityThreshold">Similarity threshold</Label>
              <Input
                id="similarityThreshold"
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={similarityThreshold}
                disabled={settingsLoading}
                onChange={(e) => setSimilarityThreshold(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="topP">Top P</Label>
              <Input
                id="topP"
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={topP}
                disabled={settingsLoading}
                onChange={(e) => setTopP(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mmrLambda">MMR lambda</Label>
              <Input
                id="mmrLambda"
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={mmrLambda}
                disabled={settingsLoading}
                onChange={(e) => setMmrLambda(e.target.value)}
              />
            </div>
            <Separator className="md:col-span-2" />
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                id="allowGeneralKnowledge"
                type="checkbox"
                checked={allowGeneralKnowledge}
                disabled={settingsLoading}
                onChange={(e) => setAllowGeneralKnowledge(e.target.checked)}
              />
              <Label htmlFor="allowGeneralKnowledge">Allow general knowledge (if enabled by platform)</Label>
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="systemPrompt">System prompt</Label>
              <textarea
                id="systemPrompt"
                className="mt-2 min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={systemPrompt}
                disabled={settingsLoading}
                onChange={(e) => setSystemPrompt(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={settingsLoading || updateSettings.isPending}>
                {updateSettings.isPending ? "Saving…" : "Save RAG settings"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
