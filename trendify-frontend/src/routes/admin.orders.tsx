import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button, Card, FormError, StatusBadge } from "@/components/Forms";
import { OrderSummary } from "@/components/OrderSummary";
import { query, useAdminList } from "@/lib/admin";
import { api } from "@/lib/api";
import { formatDate, statusLabel, type AdminOrder, type OrderStatus } from "@/lib/orders";
import { formatPrice } from "@/lib/products";

const statuses = Object.keys(statusLabel) as OrderStatus[];

export const Route = createFileRoute("/admin/orders")({
  validateSearch: (s: Record<string, unknown>): { status?: OrderStatus | undefined } => ({
    status: statuses.includes(s["status"] as OrderStatus)
      ? (s["status"] as OrderStatus)
      : undefined,
  }),
  component: AdminOrders,
});

function AdminOrders() {
  const { status: initialStatus } = Route.useSearch();
  const [status, setStatus] = useState<string>(initialStatus ?? "");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<AdminOrder | null>(null);
  const { data, error, reload } = useAdminList<AdminOrder>(
    `/admin/orders${query({ status: status || undefined, q: q.trim() || undefined })}`,
  );

  if (open)
    return (
      <OrderDetail
        order={open}
        onChange={(o) => {
          setOpen(o);
          reload();
        }}
        onClose={() => setOpen(null)}
      />
    );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Reference or email…"
          aria-label="Search orders"
          maxLength={100}
          className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Status"
          className="rounded-full border bg-card px-4 py-2 text-sm"
        >
          <option value="">All statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s}>
              {statusLabel[s]}
            </option>
          ))}
        </select>
      </div>
      <FormError error={error} />
      <div className="overflow-x-auto rounded-3xl border bg-card">
        <table className="w-full text-sm">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="p-3">Order</th>
              <th className="p-3">Customer</th>
              <th className="p-3">Placed</th>
              <th className="p-3">Total</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((o) => (
              <tr
                key={o.reference}
                className="cursor-pointer border-t hover:bg-secondary"
                onClick={() => setOpen(o)}
              >
                <td className="p-3 font-semibold">{o.reference}</td>
                <td className="p-3">{o.user_email}</td>
                <td className="p-3">{formatDate(o.created_at)}</td>
                <td className="p-3">{formatPrice(o.total_amount)}</td>
                <td className="p-3">
                  <StatusBadge status={o.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 && (
          <p className="p-6 text-center text-muted-foreground">No orders.</p>
        )}
      </div>
    </div>
  );
}

const actionLabel: Partial<Record<OrderStatus, string>> = {
  shipped: "Mark as shipped",
  delivered: "Mark as delivered",
  cancelled: "Cancel order",
  refunded: "Mark as refunded",
};

function OrderDetail({
  order,
  onChange,
  onClose,
}: {
  order: AdminOrder;
  onChange: (o: AdminOrder) => void;
  onClose: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);

  async function run(label: string, path: string, body?: unknown) {
    setBusy(label);
    try {
      const res = await api<{ order: AdminOrder }>(path, { method: body ? "PATCH" : "POST", body });
      onChange(res.order);
      toast.success("Order updated");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  const ref = encodeURIComponent(order.reference);
  return (
    <div className="space-y-4">
      <button className="text-sm text-muted-foreground" onClick={onClose}>
        ← All orders
      </button>
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card>
          <h2 className="mb-4 text-2xl">{order.reference}</h2>
          <OrderSummary order={order} />
        </Card>
        <aside className="space-y-4">
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xl">Status</h3>
              <StatusBadge status={order.status} />
            </div>
            <div className="flex flex-col gap-2">
              {order.allowed_transitions.map((s) => (
                <Button
                  key={s}
                  variant={s === "cancelled" || s === "refunded" ? "danger" : "primary"}
                  busy={busy === s}
                  onClick={() => void run(s, `/admin/orders/${ref}/status`, { status: s })}
                >
                  {actionLabel[s] ?? statusLabel[s]}
                </Button>
              ))}
              {order.allowed_transitions.length === 0 && (
                <p className="text-sm text-muted-foreground">No further changes are allowed.</p>
              )}
              {order.status === "pending_payment" && order.payment_provider === "pesapal" && (
                <Button
                  variant="outline"
                  busy={busy === "refresh"}
                  onClick={() => void run("refresh", `/admin/orders/${ref}/refresh-payment`)}
                >
                  Re-check payment with Pesapal
                </Button>
              )}
            </div>
          </Card>
          <Card>
            <h3 className="mb-2 text-xl">Customer & payment</h3>
            <dl className="space-y-1 text-sm">
              <div>
                <dt className="inline text-muted-foreground">Email: </dt>
                <dd className="inline">{order.user_email}</dd>
              </div>
              <div>
                <dt className="inline text-muted-foreground">Phone: </dt>
                <dd className="inline">{order.phone_number}</dd>
              </div>
              <div>
                <dt className="inline text-muted-foreground">Address: </dt>
                <dd className="inline">{order.shipping_address}</dd>
              </div>
              <div>
                <dt className="inline text-muted-foreground">Provider: </dt>
                <dd className="inline">{order.payment_provider ?? "—"}</dd>
              </div>
              <div>
                <dt className="inline text-muted-foreground">Payment: </dt>
                <dd className="inline">
                  {order.payment_status ?? "—"}{" "}
                  {order.payment_method && `(${order.payment_method})`}
                </dd>
              </div>
              <div>
                <dt className="inline text-muted-foreground">Tracking id: </dt>
                <dd className="inline break-all">{order.payment_tracking_id ?? "—"}</dd>
              </div>
            </dl>
          </Card>
        </aside>
      </div>
    </div>
  );
}
