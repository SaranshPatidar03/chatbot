import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addOrganizationMember,
  createOrganization,
  deleteOrganization,
  fetchOrganization,
  fetchOrganizationMembers,
  fetchOrganizations,
  removeOrganizationMember,
  updateOrganization,
  updateOrganizationMember,
} from "@/lib/organizations-api";
import { queryKeys } from "@/lib/query-keys";
import type {
  OrganizationCreatePayload,
  OrganizationMemberAddPayload,
  OrganizationMemberUpdatePayload,
  OrganizationUpdatePayload,
} from "@/types/organizations";

export function useOrganizations() {
  return useQuery({
    queryKey: queryKeys.organizations,
    queryFn: fetchOrganizations,
  });
}

export function useOrganization(orgId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.organization(orgId ?? ""),
    queryFn: () => fetchOrganization(orgId!),
    enabled: Boolean(orgId),
  });
}

export function useOrganizationMembers(orgId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.organizationMembers(orgId ?? ""),
    queryFn: () => fetchOrganizationMembers(orgId!),
    enabled: Boolean(orgId),
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrganizationCreatePayload) => createOrganization(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations });
    },
  });
}

export function useUpdateOrganization(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrganizationUpdatePayload) => updateOrganization(orgId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations });
      queryClient.invalidateQueries({ queryKey: queryKeys.organization(orgId) });
    },
  });
}

export function useDeleteOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteOrganization,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations });
    },
  });
}

export function useAddOrganizationMember(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrganizationMemberAddPayload) => addOrganizationMember(orgId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizationMembers(orgId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.organization(orgId) });
    },
  });
}

export function useUpdateOrganizationMember(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: string;
      payload: OrganizationMemberUpdatePayload;
    }) => updateOrganizationMember(orgId, userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizationMembers(orgId) });
    },
  });
}

export function useRemoveOrganizationMember(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeOrganizationMember(orgId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizationMembers(orgId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.organization(orgId) });
    },
  });
}
