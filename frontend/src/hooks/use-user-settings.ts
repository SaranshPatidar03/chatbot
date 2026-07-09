import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchUserSettings, updateUserSettings } from "@/lib/settings-api";
import { queryKeys } from "@/lib/query-keys";
import type { UserSettingsUpdate } from "@/types/settings";

export function useUserSettings() {
  return useQuery({
    queryKey: queryKeys.userSettings,
    queryFn: fetchUserSettings,
  });
}

export function useUpdateUserSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserSettingsUpdate) => updateUserSettings(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.userSettings, data);
    },
  });
}
