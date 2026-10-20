import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Button, Card, Field, FormError, Page } from "@/components/Forms";
import { api } from "@/lib/api";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Forgot password — Trendify" }] }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ message: string }>("/auth/forgot-password", {
        method: "POST",
        body: { email },
      });
      setSent(res.message);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Reset your password" narrow>
      <Card>
        {sent ? (
          <p>{sent}</p>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <FormError error={error} />
            <p className="text-sm text-muted-foreground">
              Enter your email and we'll send you a link to choose a new password. The link expires
              after 30 minutes.
            </p>
            <Field
              label="Email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" busy={busy} className="w-full">
              Send reset link
            </Button>
          </form>
        )}
        <Link to="/login" className="mt-6 inline-block text-sm underline">
          Back to sign in
        </Link>
      </Card>
    </Page>
  );
}
