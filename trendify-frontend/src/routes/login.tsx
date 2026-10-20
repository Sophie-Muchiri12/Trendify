import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button, Card, Field, FormError, Page, fieldError } from "@/components/Forms";
import { ApiError, safeRedirect } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Search = { redirect?: string | undefined };

export const Route = createFileRoute("/login")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    redirect: typeof s["redirect"] === "string" ? s["redirect"] : undefined,
  }),
  head: () => ({ meta: [{ title: "Sign in — Trendify" }] }),
  component: LoginPage,
});

function LoginPage() {
  const { redirect } = Route.useSearch();
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [needsOtp, setNeedsOtp] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await login(email, password, needsOtp ? otp : undefined);
      toast.success(`Welcome back, ${user.name.split(" ")[0]}!`);
      router.history.push(safeRedirect(redirect));
    } catch (err) {
      if (err instanceof ApiError && err.code === "mfa_required") {
        setNeedsOtp(true);
      } else {
        setError(err);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Sign in" narrow>
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <FormError error={error} />
          {!needsOtp ? (
            <>
              <Field
                label="Email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={fieldError(error, "email")}
              />
              <Field
                label="Password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </>
          ) : (
            <Field
              label="Authentication code"
              name="otp"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="\d{6}"
              maxLength={6}
              required
              autoFocus
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              hint="Enter the 6-digit code from your authenticator app."
            />
          )}
          <Button type="submit" busy={busy} className="w-full">
            {needsOtp ? "Verify and sign in" : "Sign in"}
          </Button>
        </form>
        <div className="mt-6 flex justify-between text-sm">
          <Link to="/forgot-password" className="underline">
            Forgot password?
          </Link>
          <Link to="/register" search={{ redirect }} className="underline">
            Create an account
          </Link>
        </div>
      </Card>
    </Page>
  );
}
