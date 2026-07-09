import { Building2, Plus } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useCreateOrganization, useOrganizations } from "@/hooks/use-organizations";

export function OrganizationsPage() {
  const { data, isLoading, error } = useOrganizations();
  const createOrg = useCreateOrganization();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setFormError(null);
    try {
      await createOrg.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
      });
      setName("");
      setDescription("");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Unable to create organization.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Organizations</h1>
        <p className="text-sm text-muted-foreground">
          Shared workspaces with team knowledge bases and role-based access.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create organization
          </CardTitle>
          <CardDescription>You become the owner and can invite members by email.</CardDescription>
        </CardHeader>
        <CardContent>
          {formError ? <Alert variant="destructive">{formError}</Alert> : null}
          <form onSubmit={onCreate} className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="org-name">Name</Label>
              <Input
                id="org-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Acme Research"
                required
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="org-description">Description</Label>
              <Input
                id="org-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={createOrg.isPending}>
                Create organization
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="font-display text-lg font-semibold">Your organizations</h2>
        {isLoading ? <Skeleton className="h-32 w-full" /> : null}
        {error ? <Alert variant="destructive">Failed to load organizations.</Alert> : null}
        {data?.items.length === 0 && !isLoading ? (
          <p className="text-sm text-muted-foreground">No organizations yet. Create one above.</p>
        ) : null}
        <div className="grid gap-3 md:grid-cols-2">
          {data?.items.map((org) => (
            <Card key={org.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Building2 className="h-4 w-4 text-primary" />
                    {org.name}
                  </CardTitle>
                  {org.my_role ? <Badge variant="secondary">{org.my_role}</Badge> : null}
                </div>
                <CardDescription>{org.slug}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {org.description ? (
                  <p className="text-sm text-muted-foreground">{org.description}</p>
                ) : null}
                <Button variant="outline" size="sm" asChild>
                  <Link to={`/app/organizations/${org.id}`}>Manage members</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
