import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Card, FormError, Page, RequireAuth, StatusBadge } from "@/components/Forms";
import { api } from "@/lib/api";
import { formatDate, type Order } from "@/lib/orders";
import { formatPrice } from "@/lib/products";

export const Route = createFileRoute("/account/orders/")({
  head: () => ({ meta: [{ title: "Your orders — Trendify" }] }),
  component: () => (
    <RequireAuth>
      <OrdersPage />
    </RequireAuth>
  ),
});

function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    api<{ items: Order[] }>("/orders")
      .then((r) => setOrders(r.items))
      .catch(setError);
  }, []);

  return (
    <Page title="Your orders">
      <FormError error={error} />
      {orders === null && !error && <p className="text-muted-foreground">Loading…</p>}
      {orders?.length === 0 && (
        <Card>
          <p>You haven't placed any orders yet.</p>
          <Link to="/shop" className="mt-4 inline-block underline">
            Start shopping
          </Link>
        </Card>
      )}
      <div className="space-y-4">
        {orders?.map((o) => (
          <Link
            key={o.reference}
            to="/account/orders/$ref"
            params={{ ref: o.reference }}
            className="flex flex-wrap items-center gap-4 rounded-3xl border bg-card p-4 hover:shadow-soft"
          >
            <div className="flex -space-x-3">
              {o.items.slice(0, 3).map((i) => (
                <img
                  key={`${i.product_id}-${i.size}`}
                  src={i.image_url ?? ""}
                  alt=""
                  className="h-14 w-14 rounded-2xl border-2 border-card object-cover"
                />
              ))}
            </div>
            <div className="flex-1">
              <p className="font-semibold">{o.reference}</p>
              <p className="text-sm text-muted-foreground">
                {formatDate(o.created_at)} · {o.items.reduce((s, i) => s + i.quantity, 0)} items
              </p>
            </div>
            <StatusBadge status={o.status} />
            <span className="font-bold">{formatPrice(o.total_amount)}</span>
          </Link>
        ))}
      </div>
    </Page>
  );
}
