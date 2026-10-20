import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { RequireAuth } from "@/components/Forms";

const tabs = [
  { to: "/admin", label: "Dashboard", exact: true },
  { to: "/admin/products", label: "Products" },
  { to: "/admin/orders", label: "Orders" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/reviews", label: "Reviews" },
  { to: "/admin/audit", label: "Audit log" },
] as const;

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "Admin — Trendify" }, { name: "robots", content: "noindex" }] }),
  component: () => (
    <RequireAuth admin>
      <div className="mx-auto max-w-7xl px-5 pt-10">
        <h1 className="text-4xl md:text-5xl">Admin</h1>
        <nav className="mt-6 flex flex-wrap gap-2 border-b pb-4">
          {tabs.map((t) => (
            <Link
              key={t.to}
              to={t.to}
              activeOptions={{ exact: "exact" in t }}
              className="rounded-full border bg-card px-4 py-2 text-sm"
              activeProps={{ className: "!bg-primary text-primary-foreground" }}
            >
              {t.label}
            </Link>
          ))}
        </nav>
        <div className="pt-6">
          <Outlet />
        </div>
      </div>
    </RequireAuth>
  ),
});
