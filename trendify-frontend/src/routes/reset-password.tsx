import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Button,
  Card,
  Field,
  FormError,
  Page,
  PASSWORD_HINT,
  fieldError,
} from "@/components/Forms";
import { api } from "@/lib/api";

export const Route = createFileRoute("/reset-password")({
  validateSearch: (s: Record<string, unknown>): { token?: string | undefined } => ({
    token: typeof s["token"] === "string" ? s["token"] : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Choose a new password — Trendify" },
      { name: "referrer", content: "no-referrer" },
    ],
  }),
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  const { token: tokenFromUrl } = Route.useSearch();
  // Keep the token in memory only, and drop it from the address bar and history.
  const [token] = useState(tokenFromUrl);
  useEffect(() => {
    if (tokenFromUrl) window.history.replaceState(null, "", "/reset-password");
  }, [tokenFromUrl]);
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) return setError(new Error("The passwords don't match."));
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: { token, password },
      });
      toast.success(res.message);
      void navigate({ to: "/login" });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (!token)
    return (
      <Page title="Choose a new password" narrow>
        <Card>
          <p>This link is missing its token.</p>
          <Link to="/forgot-password" className="mt-4 inline-block underline">
            Request a new link
          </Link>
        </Card>
      </Page>
    );

  return (
    <Page title="Choose a new password" narrow>
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <FormError error={error} />
          <Field
            label="New password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={10}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fieldError(error, "password")}
            hint={PASSWORD_HINT}
          />
          <Field
            label="Confirm new password"
            name="confirm"
            type="password"
            autoComplete="new-password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
          <Button type="submit" busy={busy} className="w-full">
            Save new password
          </Button>
        </form>
      </Card>
    </Page>
  );
}
