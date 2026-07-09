import { Link, useSearchParams } from "react-router-dom";
import { FormEvent, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { verifyEmailRequest } from "@/lib/auth-api";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const tokenFromUrl = params.get("token") ?? "";
  const [token, setToken] = useState(tokenFromUrl);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      await verifyEmailRequest(token.trim());
      setMessage("Email verified. You can sign in now.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Verify your email</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Paste the verification token from your email or use the link we sent you.
        </p>
      </div>
      {message ? <Alert variant="success">{message}</Alert> : null}
      {error ? <Alert variant="destructive">{error}</Alert> : null}
      <form onSubmit={onSubmit} className="space-y-4">
        <input
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Verification token"
          required
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Verifying…" : "Verify email"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        <Link to="/login" className="text-primary hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
