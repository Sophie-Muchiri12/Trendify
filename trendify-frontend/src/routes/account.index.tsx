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
  RequireAuth,
  fieldError,
} from "@/components/Forms";
import { api } from "@/lib/api";
import { useAuth, type User } from "@/lib/auth";

export const Route = createFileRoute("/account/")({
  head: () => ({ meta: [{ title: "Your account — Trendify" }] }),
  component: () => (
    <RequireAuth>
      <AccountPage />
    </RequireAuth>
  ),
});

function AccountPage() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <Page title="Your account">
      <div className="mb-8 flex flex-wrap gap-3">
        <Link to="/account/orders" className="rounded-full border bg-card px-5 py-2 text-sm">
          Your orders
        </Link>
        {user.role === "admin" && (
          <Link
            to="/admin"
            className="rounded-full bg-primary px-5 py-2 text-sm text-primary-foreground"
          >
            Admin dashboard
          </Link>
        )}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {!user.email_verified && <VerifyBanner />}
        <ProfileCard user={user} />
        <PasswordCard />
        <MfaCard user={user} />
        <SessionsCard />
        <MyReviews />
        <CloseAccountCard />
      </div>
    </Page>
  );
}

function VerifyBanner() {
  const [busy, setBusy] = useState(false);
  return (
    <Card className="border-ochre bg-ochre/10 lg:col-span-2">
      <h2 className="text-2xl">Verify your email</h2>
      <p className="mt-2 text-sm">
        We sent you a verification link when you signed up. You need to verify your email before you
        can place orders or write reviews.
      </p>
      <Button
        className="mt-4"
        variant="outline"
        busy={busy}
        onClick={async () => {
          setBusy(true);
          try {
            const res = await api<{ message: string }>("/auth/resend-verification", {
              method: "POST",
            });
            toast.success(res.message);
          } catch (err) {
            toast.error((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        Send a new link
      </Button>
    </Card>
  );
}

function ProfileCard({ user }: { user: User }) {
  const { setUser } = useAuth();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone_number);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ user: User }>("/account", {
        method: "PATCH",
        body: { name, phone_number: phone },
      });
      setUser(res.user);
      toast.success("Profile saved");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-4 text-2xl">Profile</h2>
      <form onSubmit={save} className="space-y-4">
        <FormError error={error} />
        <Field
          label="Email"
          name="email"
          value={user.email}
          disabled
          readOnly
          hint={user.email_verified ? "Verified" : "Not verified yet"}
        />
        <Field
          label="Full name"
          name="name"
          required
          maxLength={120}
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={fieldError(error, "name")}
        />
        <Field
          label="Phone number"
          name="phone_number"
          type="tel"
          required
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          error={fieldError(error, "phone_number")}
        />
        <Button type="submit" busy={busy}>
          Save changes
        </Button>
      </form>
    </Card>
  );
}

function PasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ message: string }>("/account/change-password", {
        method: "POST",
        body: { current_password: current, new_password: next },
      });
      toast.success(res.message);
      setCurrent("");
      setNext("");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-4 text-2xl">Change password</h2>
      <form onSubmit={save} className="space-y-4">
        <FormError error={error} />
        <Field
          label="Current password"
          name="current_password"
          type="password"
          autoComplete="current-password"
          required
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
        />
        <Field
          label="New password"
          name="new_password"
          type="password"
          autoComplete="new-password"
          required
          minLength={10}
          value={next}
          onChange={(e) => setNext(e.target.value)}
          error={fieldError(error, "new_password")}
          hint={PASSWORD_HINT}
        />
        <Button type="submit" busy={busy}>
          Update password
        </Button>
      </form>
    </Card>
  );
}

function MfaCard({ user }: { user: User }) {
  const { setUser } = useAuth();
  const [step, setStep] = useState<"idle" | "password" | "code" | "disable">("idle");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setStep("idle");
    setPassword("");
    setCode("");
    setSetup(null);
    setError(null);
  };

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-2 text-2xl">Two-factor authentication</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        {user.mfa_enabled
          ? "On. You'll be asked for a code from your authenticator app when you sign in."
          : "Add a second step to sign-in with an authenticator app such as Google Authenticator or Authy."}
      </p>
      <FormError error={error} />

      {step === "idle" &&
        (user.mfa_enabled ? (
          <Button variant="danger" onClick={() => setStep("disable")}>
            Turn off
          </Button>
        ) : (
          <Button onClick={() => setStep("password")}>Set up</Button>
        ))}

      {step === "password" && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              setSetup(await api("/account/mfa/setup", { method: "POST", body: { password } }));
              setPassword("");
              setStep("code");
            });
          }}
        >
          <Field
            label="Confirm your password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="flex gap-2">
            <Button type="submit" busy={busy}>
              Continue
            </Button>
            <Button type="button" variant="outline" onClick={reset}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {step === "code" && setup && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              const res = await api<{ user: User }>("/account/mfa/enable", {
                method: "POST",
                body: { code },
              });
              setUser(res.user);
              toast.success("Two-factor authentication is on");
              reset();
            });
          }}
        >
          <ol className="list-decimal space-y-2 pl-5 text-sm">
            <li>
              In your authenticator app, add an account and enter this key (or{" "}
              <a className="underline" href={setup.otpauth_uri}>
                open it in the app
              </a>{" "}
              on your phone):
            </li>
          </ol>
          <code className="block select-all break-all rounded-2xl bg-secondary px-4 py-3 text-center font-mono text-base tracking-widest">
            {setup.secret.match(/.{1,4}/g)?.join(" ")}
          </code>
          <Field
            label="Enter the 6-digit code it shows"
            name="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="\d{6}"
            maxLength={6}
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            error={fieldError(error, "code")}
          />
          <div className="flex gap-2">
            <Button type="submit" busy={busy}>
              Turn on
            </Button>
            <Button type="button" variant="outline" onClick={reset}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {step === "disable" && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              const res = await api<{ user: User }>("/account/mfa/disable", {
                method: "POST",
                body: { password, code },
              });
              setUser(res.user);
              toast.success("Two-factor authentication is off");
              reset();
            });
          }}
        >
          <Field
            label="Password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Field
            label="Current 6-digit code"
            name="code"
            inputMode="numeric"
            pattern="\d{6}"
            maxLength={6}
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          />
          <div className="flex gap-2">
            <Button type="submit" variant="danger" busy={busy}>
              Turn off
            </Button>
            <Button type="button" variant="outline" onClick={reset}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}

function SessionsCard() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  return (
    <Card>
      <h2 className="mb-2 text-2xl">Sessions</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Lost a device or signed in somewhere public? Sign out of Trendify on every device, including
        this one.
      </p>
      <Button
        variant="outline"
        busy={busy}
        onClick={async () => {
          setBusy(true);
          try {
            await api("/auth/logout-all", { method: "POST" });
            setUser(null);
            toast.success("Signed out on all devices");
            void navigate({ to: "/login" });
          } catch (err) {
            toast.error((err as Error).message);
            setBusy(false);
          }
        }}
      >
        Sign out everywhere
      </Button>
    </Card>
  );
}

interface MyReview {
  review_id: number;
  rating: number;
  review_text: string | null;
  status: "pending" | "approved" | "rejected";
  product_slug: string | null;
  product_name: string | null;
}

function MyReviews() {
  const [reviews, setReviews] = useState<MyReview[] | null>(null);
  useEffect(() => {
    api<{ items: MyReview[] }>("/account/reviews")
      .then((r) => setReviews(r.items))
      .catch(() => setReviews([]));
  }, []);
  return (
    <Card>
      <h2 className="mb-4 text-2xl">Your reviews</h2>
      {reviews === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : reviews.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          You haven't reviewed anything yet. You can review products after you've bought them.
        </p>
      ) : (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <li key={r.review_id} className="flex items-center justify-between gap-3 text-sm">
              <span>
                {r.product_slug ? (
                  <Link
                    to="/product/$id"
                    params={{ id: r.product_slug }}
                    className="font-semibold underline"
                  >
                    {r.product_name}
                  </Link>
                ) : (
                  r.product_name
                )}{" "}
                · {"★".repeat(r.rating)}
              </span>
              <span className="rounded-full bg-secondary px-3 py-1 text-xs capitalize">
                {r.status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function CloseAccountCard() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  return (
    <Card className="lg:col-span-2">
      <h2 className="mb-2 text-2xl">Close account</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        This removes your personal details and reviews and signs you out. Order records are kept for
        accounting, without your name or contact details.
      </p>
      {!open ? (
        <Button variant="danger" onClick={() => setOpen(true)}>
          Close my account
        </Button>
      ) : (
        <form
          className="max-w-sm space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError(null);
            try {
              await api("/account", { method: "DELETE", body: { password } });
              setUser(null);
              toast.success("Your account has been closed");
              void navigate({ to: "/" });
            } catch (err) {
              setError(err);
              setBusy(false);
            }
          }}
        >
          <FormError error={error} />
          <Field
            label="Confirm your password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="flex gap-2">
            <Button type="submit" variant="danger" busy={busy}>
              Close account permanently
            </Button>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
}
