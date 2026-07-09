import { Link } from "react-router-dom";
import { FormEvent, useState } from "react";
import axios from "axios";

import { useAuthContext } from "@/app/auth-provider";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ForgotPasswordPage() {
  const { forgotPassword } = useAuthContext();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      await forgotPassword({ email: email.trim().toLowerCase() });
      setMessage("If that email exists, a reset link has been sent.");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setError("Password reset API is not available yet. Complete Phase 4 backend setup.");
      } else {
        setError(err instanceof Error ? err.message : "Unable to send reset email.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Reset password</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter your email and we will send reset instructions.
        </p>
      </div>
      {message ? <Alert variant="success">{message}</Alert> : null}
      {error ? <Alert variant="destructive">{error}</Alert> : null}
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Sending…" : "Send reset link"}
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
