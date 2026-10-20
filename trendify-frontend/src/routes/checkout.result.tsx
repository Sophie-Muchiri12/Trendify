import { createFileRoute, Link } from "@tanstack/react-router";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, FormError, Page, RequireAuth } from "@/components/Forms";
import { api } from "@/lib/api";
import type { Order } from "@/lib/orders";

/**
 * Where Pesapal sends the customer back after paying. The query string is not trusted:
 * we ask our server, which confirms the payment with Pesapal directly.
 */
export const Route = createFileRoute("/checkout/result")({
  validateSearch: (s: Record<string, unknown>): { ref?: string | undefined } => ({
    ref: typeof s["ref"] === "string" ? s["ref"] : undefined,
  }),
  head: () => ({ meta: [{ title: "Payment result — Trendify" }] }),
  component: () => (
    <RequireAuth>
      <ResultPage />
    </RequireAuth>
  ),
});

function ResultPage() {
  const { ref } = Route.useSearch();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!ref) return;
    let attempts = 0;
    let timer: ReturnType<typeof setTimeout>;
    const check = () =>
      api<{ order: Order }>(`/orders/${encodeURIComponent(ref)}/refresh-payment`, {
        method: "POST",
      })
        .then(({ order: o }) => {
          setOrder(o);
          // Payment confirmation can take a few seconds to reach Pesapal's status API.
          if (o.status === "pending_payment" && o.payment_status !== "failed" && ++attempts < 10)
            timer = setTimeout(() => void check(), 3000);
        })
        .catch(setError);
    void check();
    return () => clearTimeout(timer);
  }, [ref]);

  const paid = order && order.status !== "pending_payment" && order.status !== "cancelled";
  const failed = order?.payment_status === "failed" || order?.payment_status === "reversed";

  return (
    <Page title="Payment" narrow>
      <Card className="text-center">
        <FormError error={error} />
        {!order && !error && <p>Checking your payment…</p>}
        {order && paid && (
          <>
            <CheckCircle2 className="mx-auto h-14 w-14 text-green-700" />
            <h2 className="mt-4 text-3xl">Thank you!</h2>
            <p className="mt-2 text-muted-foreground">
              Order {order.reference} is paid. We'll let you know when it ships.
            </p>
          </>
        )}
        {order && !paid && failed && (
          <>
            <XCircle className="mx-auto h-14 w-14 text-destructive" />
            <h2 className="mt-4 text-3xl">Payment didn't go through</h2>
            <p className="mt-2 text-muted-foreground">
              Your order is saved. You can try paying again.
            </p>
          </>
        )}
        {order && !paid && !failed && (
          <>
            <Clock className="mx-auto h-14 w-14 text-ochre" />
            <h2 className="mt-4 text-3xl">Confirming your payment</h2>
            <p className="mt-2 text-muted-foreground">
              This can take a moment. You can safely leave this page; your order updates
              automatically.
            </p>
          </>
        )}
        {order && (
          <Link
            to="/account/orders/$ref"
            params={{ ref: order.reference }}
            className="mt-6 inline-block rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
          >
            View order
          </Link>
        )}
      </Card>
    </Page>
  );
}
