import { api } from "@/lib/api";
import type {
  OrganizationCreatePayload,
  OrganizationDetail,
  OrganizationListResponse,
  OrganizationMember,
  OrganizationMemberAddPayload,
  OrganizationMemberListResponse,
  OrganizationMemberUpdatePayload,
  OrganizationSummary,
  OrganizationUpdatePayload,
} from "@/types/organizations";

export async function fetchOrganizations(): Promise<OrganizationListResponse> {
  const { data } = await api.get<OrganizationListResponse>("/organizations");
  return data;
}

export async function fetchOrganization(orgId: string): Promise<OrganizationDetail> {
  const { data } = await api.get<OrganizationDetail>(`/organizations/${orgId}`);
  return data;
}

export async function createOrganization(
  payload: OrganizationCreatePayload,
): Promise<OrganizationDetail> {
  const { data } = await api.post<OrganizationDetail>("/organizations", payload);
  return data;
}

export async function updateOrganization(
  orgId: string,
  payload: OrganizationUpdatePayload,
): Promise<OrganizationDetail> {
  const { data } = await api.patch<OrganizationDetail>(`/organizations/${orgId}`, payload);
  return data;
}

export async function deleteOrganization(orgId: string): Promise<void> {
  await api.delete(`/organizations/${orgId}`);
}

export async function fetchOrganizationMembers(
  orgId: string,
): Promise<OrganizationMemberListResponse> {
  const { data } = await api.get<OrganizationMemberListResponse>(
    `/organizations/${orgId}/members`,
  );
  return data;
}

export async function addOrganizationMember(
  orgId: string,
  payload: OrganizationMemberAddPayload,
): Promise<OrganizationMember> {
  const { data } = await api.post<OrganizationMember>(`/organizations/${orgId}/members`, payload);
  return data;
}

export async function updateOrganizationMember(
  orgId: string,
  userId: string,
  payload: OrganizationMemberUpdatePayload,
): Promise<OrganizationMember> {
  const { data } = await api.patch<OrganizationMember>(
    `/organizations/${orgId}/members/${userId}`,
    payload,
  );
  return data;
}

export async function removeOrganizationMember(orgId: string, userId: string): Promise<void> {
  await api.delete(`/organizations/${orgId}/members/${userId}`);
}

export type { OrganizationSummary };
