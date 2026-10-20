import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button, Card, FormError, Page, RequireAuth, StatusBadge } from "@/components/Forms";
import { OrderSummary } from "@/components/OrderSummary";
import { api } from "@/lib/api";
import { formatDate, goToPayment, statusLabel, type Order, type OrderStatus } from "@/lib/orders";
import { formatPrice, invalidateProducts } from "@/lib/products";

export const Route = createFileRoute("/account/orders/$ref")({
  head: ({ params }) => ({ meta: [{ title: `Order ${params.ref} — Trendify` }] }),
  component: () => (
    <RequireAuth>
      <OrderPage />
    </RequireAuth>
  ),
});

const TIMELINE: OrderStatus[] = ["pending_payment", "paid", "shipped", "delivered"];

function OrderPage() {
  const { ref } = Route.useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<"pay" | "cancel" | null>(null);

  useEffect(() => {
    api<{ order: Order }>(`/orders/${encodeURIComponent(ref)}`)
      .then((r) => setOrder(r.order))
      .catch(setError);
  }, [ref]);

  async function pay() {
    setBusy("pay");
    try {
      const res = await api<{ order: Order; payment_url: string | null }>(
        `/orders/${encodeURIComponent(ref)}/pay`,
        { method: "POST" },
      );
      setOrder(res.order);
      if (res.payment_url) goToPayment(res.payment_url, (p) => void navigate({ to: p }));
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function cancel() {
    setBusy("cancel");
    try {
      const res = await api<{ order: Order }>(`/orders/${encodeURIComponent(ref)}/cancel`, {
        method: "POST",
      });
      setOrder(res.order);
      invalidateProducts();
      toast.success("Order cancelled");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  if (error)
    return (
      <Page title="Order">
        <FormError error={error} />
        <Link to="/account/orders" className="mt-4 inline-block underline">
          Back to your orders
        </Link>
      </Page>
    );
  if (!order) return <p className="py-32 text-center text-muted-foreground">Loading…</p>;

  const step = TIMELINE.indexOf(order.status);
  return (
    <Page title={`Order ${order.reference}`}>
      <Link to="/account/orders" className="text-sm text-muted-foreground">
        ← All orders
      </Link>
      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card>
          <OrderSummary order={order} />
        </Card>
        <aside className="space-y-6">
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl">Status</h2>
              <StatusBadge status={order.status} />
            </div>
            {step >= 0 ? (
              <ol className="space-y-2 text-sm">
                {TIMELINE.map((s, i) => (
                  <li key={s} className={i <= step ? "font-semibold" : "text-muted-foreground"}>
                    {i <= step ? "●" : "○"} {statusLabel[s]}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">
                This order was {statusLabel[order.status].toLowerCase()}.
              </p>
            )}
            {order.payment_status === "failed" && order.can_pay && (
              <p className="mt-3 text-sm text-destructive">The last payment attempt failed.</p>
            )}
            <div className="mt-6 flex flex-col gap-2">
              {order.can_pay && (
                <Button variant="accent" busy={busy === "pay"} onClick={pay}>
                  Pay now
                </Button>
              )}
              {order.can_cancel && (
                <Button variant="outline" busy={busy === "cancel"} onClick={cancel}>
                  Cancel order
                </Button>
              )}
            </div>
          </Card>
          <Card>
            <h2 className="mb-2 text-2xl">Delivery</h2>
            <p className="text-sm">{order.shipping_address}</p>
            <p className="text-sm text-muted-foreground">{order.phone_number}</p>
            <p className="mt-3 text-xs text-muted-foreground">
              Placed {formatDate(order.created_at)}
            </p>
            {order.paid_at && (
              <p className="text-xs text-muted-foreground">
                Paid {formatDate(order.paid_at)}
                {order.payment_method && ` · ${order.payment_method}`}
              </p>
            )}
          </Card>
        </aside>
      </div>
    </Page>
  );
}
