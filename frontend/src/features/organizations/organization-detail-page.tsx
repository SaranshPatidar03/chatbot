import axios from "axios";
import { ArrowLeft, UserMinus, UserPlus } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuthContext } from "@/app/auth-provider";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAddOrganizationMember,
  useDeleteOrganization,
  useOrganization,
  useOrganizationMembers,
  useRemoveOrganizationMember,
  useUpdateOrganizationMember,
} from "@/hooks/use-organizations";

function formatError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export function OrganizationDetailPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthContext();
  const orgQuery = useOrganization(orgId);
  const membersQuery = useOrganizationMembers(orgId);
  const addMember = useAddOrganizationMember(orgId ?? "");
  const updateMember = useUpdateOrganizationMember(orgId ?? "");
  const removeMember = useRemoveOrganizationMember(orgId ?? "");
  const deleteOrg = useDeleteOrganization();

  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  const org = orgQuery.data;
  const canManage = org?.my_role === "owner" || org?.my_role === "admin";
  const isOwner = org?.my_role === "owner";

  async function onInvite(event: FormEvent) {
    event.preventDefault();
    if (!email.trim()) return;
    setError(null);
    try {
      await addMember.mutateAsync({ email: email.trim().toLowerCase(), role: "member" });
      setEmail("");
    } catch (err) {
      setError(formatError(err));
    }
  }

  async function onDeleteOrg() {
    if (!orgId || !window.confirm("Delete this organization and its shared knowledge base?")) return;
    try {
      await deleteOrg.mutateAsync(orgId);
      navigate("/app/organizations");
    } catch (err) {
      setError(formatError(err));
    }
  }

  if (orgQuery.isLoading) return <Skeleton className="h-64 w-full" />;
  if (!org) return <Alert variant="destructive">Organization not found.</Alert>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/app/organizations">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </Button>
        <div className="flex-1">
          <h1 className="font-display text-2xl font-bold">{org.name}</h1>
          <p className="text-sm text-muted-foreground">
            {org.member_count} members · {org.slug}
          </p>
        </div>
        {org.my_role ? <Badge>{org.my_role}</Badge> : null}
      </div>

      {error ? <Alert variant="destructive">{error}</Alert> : null}

      {canManage ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Invite member
            </CardTitle>
            <CardDescription>User must already have an account with this email.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onInvite} className="flex flex-wrap gap-2">
              <Input
                type="email"
                placeholder="colleague@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="max-w-sm"
                required
              />
              <Button type="submit" disabled={addMember.isPending}>
                Add member
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Members</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {membersQuery.isLoading ? <Skeleton className="h-24 w-full" /> : null}
          {membersQuery.data?.items.map((member) => (
            <div
              key={member.user_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/70 p-3"
            >
              <div>
                <p className="text-sm font-medium">{member.full_name ?? member.email}</p>
                <p className="text-xs text-muted-foreground">{member.email}</p>
              </div>
              <div className="flex items-center gap-2">
                {canManage && isOwner && member.user_id !== user?.id ? (
                  <select
                    className="rounded-md border border-border bg-background px-2 py-1 text-sm"
                    value={member.role}
                    onChange={(e) =>
                      updateMember.mutate({
                        userId: member.user_id,
                        payload: { role: e.target.value as "owner" | "admin" | "member" },
                      })
                    }
                  >
                    <option value="member">member</option>
                    <option value="admin">admin</option>
                    <option value="owner">owner</option>
                  </select>
                ) : (
                  <Badge variant="secondary">{member.role}</Badge>
                )}
                {(canManage && member.user_id !== user?.id) || member.user_id === user?.id ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Remove member"
                    onClick={() => removeMember.mutate(member.user_id)}
                  >
                    <UserMinus className="h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {isOwner ? (
        <Button variant="outline" className="text-destructive" onClick={onDeleteOrg} disabled={deleteOrg.isPending}>
          Delete organization
        </Button>
      ) : null}
    </div>
  );
}
