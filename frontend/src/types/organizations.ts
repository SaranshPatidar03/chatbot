export type OrganizationSummary = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  my_role: string | null;
};

export type OrganizationDetail = OrganizationSummary & {
  member_count: number;
  created_by_id: string | null;
};

export type OrganizationListResponse = {
  items: OrganizationSummary[];
  total: number;
};

export type OrganizationMember = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  joined_at: string;
};

export type OrganizationMemberListResponse = {
  items: OrganizationMember[];
  total: number;
};

export type OrganizationCreatePayload = {
  name: string;
  description?: string | null;
  slug?: string | null;
};

export type OrganizationUpdatePayload = {
  name?: string;
  description?: string | null;
};

export type OrganizationMemberAddPayload = {
  email: string;
  role?: "admin" | "member";
};

export type OrganizationMemberUpdatePayload = {
  role: "owner" | "admin" | "member";
};
