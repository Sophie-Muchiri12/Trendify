import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Card, FormError } from "@/components/Forms";
import { api } from "@/lib/api";
import { statusLabel, type OrderStatus } from "@/lib/orders";
import { formatPrice } from "@/lib/products";

interface Stats {
  users: number;
  products: number;
  low_stock: number;
  orders_by_status: Partial<Record<OrderStatus, number>>;
  revenue: number;
  pending_reviews: number;
  security_events_24h: number;
}

export const Route = createFileRoute("/admin/")({ component: Dashboard });

function Tile({ label, value, to }: { label: string; value: string | number; to?: string }) {
  const body = (
    <Card className="h-full">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </Card>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    api<Stats>("/admin/stats").then(setStats).catch(setError);
  }, []);
  if (error) return <FormError error={error} />;
  if (!stats) return <p className="text-muted-foreground">Loading…</p>;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Tile label="Revenue (paid orders)" value={formatPrice(stats.revenue)} />
        <Tile label="Active customers & staff" value={stats.users} to="/admin/users" />
        <Tile label="Products on sale" value={stats.products} to="/admin/products" />
        <Tile label="Low stock (< 5)" value={stats.low_stock} to="/admin/products" />
        <Tile label="Reviews to moderate" value={stats.pending_reviews} to="/admin/reviews" />
        <Tile label="Security events (24h)" value={stats.security_events_24h} to="/admin/audit" />
      </div>
      <Card>
        <h2 className="mb-4 text-2xl">Orders by status</h2>
        <div className="flex flex-wrap gap-3">
          {(Object.keys(statusLabel) as OrderStatus[]).map((s) => (
            <Link
              key={s}
              to="/admin/orders"
              search={{ status: s }}
              className="rounded-2xl border px-4 py-3 text-sm"
            >
              <span className="text-muted-foreground">{statusLabel[s]}</span>
              <span className="ml-3 font-semibold">{stats.orders_by_status[s] ?? 0}</span>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
