import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Button, Card, FormError, Page, RequireAuth } from "@/components/Forms";
import { OrderSummary } from "@/components/OrderSummary";
import { api } from "@/lib/api";
import type { Order } from "@/lib/orders";

/**
 * Development stand-in for Pesapal's hosted payment page. The backend only accepts these
 * calls when PAYMENT_PROVIDER=simulated and never in production.
 */
export const Route = createFileRoute("/checkout/simulate")({
  validateSearch: (s: Record<string, unknown>): { ref?: string | undefined } => ({
    ref: typeof s["ref"] === "string" ? s["ref"] : undefined,
  }),
  head: () => ({ meta: [{ title: "Payment (simulator) — Trendify" }] }),
  component: () => (
    <RequireAuth>
      <SimulatePage />
    </RequireAuth>
  ),
});

function SimulatePage() {
  const { ref } = Route.useSearch();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ref)
      api<{ order: Order }>(`/orders/${encodeURIComponent(ref)}`)
        .then((r) => setOrder(r.order))
        .catch(setError);
  }, [ref]);

  async function finish(outcome: "success" | "failure") {
    if (!ref) return;
    setBusy(true);
    try {
      await api(`/payments/simulated/${encodeURIComponent(ref)}`, {
        method: "POST",
        body: { outcome },
      });
      void navigate({ to: "/checkout/result", search: { ref } });
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  return (
    <Page title="Payment simulator" narrow>
      <Card>
        <p className="mb-4 rounded-2xl bg-ochre/15 px-4 py-3 text-sm">
          Development mode: no real payment is taken. With Pesapal configured, customers see
          Pesapal's secure payment page here instead.
        </p>
        <FormError error={error} />
        {order && <OrderSummary order={order} />}
        <div className="mt-6 flex flex-col gap-2">
          <Button variant="accent" busy={busy} disabled={!order} onClick={() => finish("success")}>
            Simulate successful payment
          </Button>
          <Button variant="outline" busy={busy} disabled={!order} onClick={() => finish("failure")}>
            Simulate failed payment
          </Button>
        </div>
      </Card>
    </Page>
  );
}
