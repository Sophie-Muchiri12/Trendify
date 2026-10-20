import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
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

export const Route = createFileRoute("/register")({
  validateSearch: (s: Record<string, unknown>): { redirect?: string | undefined } => ({
    redirect: typeof s["redirect"] === "string" ? s["redirect"] : undefined,
  }),
  head: () => ({ meta: [{ title: "Create an account — Trendify" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const [form, setForm] = useState({ name: "", email: "", phone_number: "", password: "" });
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password !== confirm) {
      setError(new Error("The passwords don't match."));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ message: string }>("/auth/register", { method: "POST", body: form });
      setDone(res.message);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (done)
    return (
      <Page title="Check your email" narrow>
        <Card>
          <p>{done}</p>
          <p className="mt-3 text-sm text-muted-foreground">
            Once your email is verified you can place orders and write reviews.
          </p>
          <Link to="/login" className="mt-6 inline-block underline">
            Go to sign in
          </Link>
        </Card>
      </Page>
    );

  return (
    <Page title="Create an account" narrow>
      <Card>
        <form onSubmit={submit} className="space-y-4">
          <FormError error={error} />
          <Field
            label="Full name"
            name="name"
            autoComplete="name"
            required
            maxLength={120}
            value={form.name}
            onChange={set("name")}
            error={fieldError(error, "name")}
          />
          <Field
            label="Email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={set("email")}
            error={fieldError(error, "email")}
          />
          <Field
            label="Phone number"
            name="phone_number"
            type="tel"
            autoComplete="tel"
            required
            placeholder="+254712345678"
            value={form.phone_number}
            onChange={set("phone_number")}
            error={fieldError(error, "phone_number")}
          />
          <Field
            label="Password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={10}
            value={form.password}
            onChange={set("password")}
            error={fieldError(error, "password")}
            hint={PASSWORD_HINT}
          />
          <Field
            label="Confirm password"
            name="confirm"
            type="password"
            autoComplete="new-password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
          <Button type="submit" busy={busy} className="w-full">
            Create account
          </Button>
        </form>
        <p className="mt-6 text-sm">
          Already have an account?{" "}
          <Link to="/login" className="underline">
            Sign in
          </Link>
        </p>
      </Card>
    </Page>
  );
}
