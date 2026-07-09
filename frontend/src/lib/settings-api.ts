import { api } from "@/lib/api";
import type { UserSettings, UserSettingsUpdate } from "@/types/settings";

export async function fetchUserSettings(): Promise<UserSettings> {
  const { data } = await api.get<UserSettings>("/settings");
  return data;
}

export async function updateUserSettings(payload: UserSettingsUpdate): Promise<UserSettings> {
  const { data } = await api.patch<UserSettings>("/settings", payload);
  return data;
}
