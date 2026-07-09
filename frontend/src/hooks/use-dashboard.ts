import { useQuery } from "@tanstack/react-query";

import { fetchDashboardSummary } from "@/lib/dashboard-api";
import { queryKeys } from "@/lib/query-keys";

export function useDashboardSummary() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: fetchDashboardSummary,
  });
}
