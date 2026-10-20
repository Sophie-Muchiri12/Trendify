import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Card, Page } from "@/components/Forms";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/verify-email")({
  validateSearch: (s: Record<string, unknown>): { token?: string | undefined } => ({
    token: typeof s["token"] === "string" ? s["token"] : undefined,
  }),
  head: () => ({
    meta: [{ title: "Verify email — Trendify" }, { name: "referrer", content: "no-referrer" }],
  }),
  component: VerifyEmailPage,
});

function VerifyEmailPage() {
  const { token } = Route.useSearch();
  const { reload } = useAuth();
  const [state, setState] = useState<"working" | "ok" | "error">(token ? "working" : "error");
  const [message, setMessage] = useState("This link is missing its token.");
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    // Remove the token from the address bar and browser history.
    window.history.replaceState(null, "", "/verify-email");
    api<{ message: string }>("/auth/verify-email", { method: "POST", body: { token } })
      .then((res) => {
        setState("ok");
        setMessage(res.message);
        void reload();
      })
      .catch((err: Error) => {
        setState("error");
        setMessage(err.message);
      });
  }, [token, reload]);

  return (
    <Page title="Verify your email" narrow>
      <Card>
        <p role={state === "error" ? "alert" : undefined}>
          {state === "working" ? "Verifying…" : message}
        </p>
        <Link to={state === "ok" ? "/shop" : "/account"} className="mt-6 inline-block underline">
          {state === "ok" ? "Start shopping" : "Go to your account to request a new link"}
        </Link>
      </Card>
    </Page>
  );
}
