import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { FormError } from "@/components/Forms";
import { query, useAdminList } from "@/lib/admin";
import { api } from "@/lib/api";
import { useAuth, type User } from "@/lib/auth";
import { formatDate } from "@/lib/orders";

interface AdminUser extends User {
  is_active: boolean;
  locked: boolean;
  failed_login_count: number;
  last_login_at: string | null;
  order_count: number;
}

export const Route = createFileRoute("/admin/users")({ component: AdminUsers });

function AdminUsers() {
  const { user: me } = useAuth();
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const { data, error, reload } = useAdminList<AdminUser>(
    `/admin/users${query({ q: q.trim() || undefined, role: role || undefined })}`,
  );

  async function update(
    u: AdminUser,
    body: Partial<Pick<AdminUser, "role" | "is_active">>,
    done: string,
  ) {
    try {
      await api(`/admin/users/${u.user_id}`, { method: "PATCH", body });
      toast.success(done);
      reload();
    } catch (err) {
      toast.error((err as Error).message);
    }
  }

  async function unlock(u: AdminUser) {
    try {
      await api(`/admin/users/${u.user_id}/unlock`, { method: "POST" });
      toast.success(`${u.email} unlocked`);
      reload();
    } catch (err) {
      toast.error((err as Error).message);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Name or email…"
          aria-label="Search users"
          maxLength={100}
          className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          aria-label="Role"
          className="rounded-full border bg-card px-4 py-2 text-sm"
        >
          <option value="">All roles</option>
          <option value="customer">Customers</option>
          <option value="admin">Administrators</option>
        </select>
      </div>
      <FormError error={error} />
      <div className="overflow-x-auto rounded-3xl border bg-card">
        <table className="w-full text-sm">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="p-3">User</th>
              <th className="p-3">Role</th>
              <th className="p-3">Status</th>
              <th className="p-3">Last sign-in</th>
              <th className="p-3">Orders</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((u) => {
              const self = u.user_id === me?.user_id;
              return (
                <tr key={u.user_id} className="border-t">
                  <td className="p-3">
                    <p className="font-semibold">{u.name}</p>
                    <p className="text-muted-foreground">{u.email}</p>
                  </td>
                  <td className="p-3 capitalize">{u.role}</td>
                  <td className="p-3">
                    {!u.is_active ? "Deactivated" : u.locked ? "Locked" : "Active"}
                    {u.mfa_enabled && " · 2FA"}
                    {!u.email_verified && " · unverified"}
                  </td>
                  <td className="p-3">{formatDate(u.last_login_at) || "—"}</td>
                  <td className="p-3">{u.order_count}</td>
                  <td className="space-x-3 whitespace-nowrap p-3 text-right">
                    {!self && (
                      <>
                        <button
                          className="underline"
                          onClick={() =>
                            void update(
                              u,
                              { role: u.role === "admin" ? "customer" : "admin" },
                              u.role === "admin" ? "Admin access removed" : "Made administrator",
                            )
                          }
                        >
                          {u.role === "admin" ? "Remove admin" : "Make admin"}
                        </button>
                        <button
                          className="underline"
                          onClick={() =>
                            void update(
                              u,
                              { is_active: !u.is_active },
                              u.is_active ? "User deactivated" : "User reactivated",
                            )
                          }
                        >
                          {u.is_active ? "Deactivate" : "Reactivate"}
                        </button>
                      </>
                    )}
                    {u.locked && (
                      <button className="underline" onClick={() => void unlock(u)}>
                        Unlock
                      </button>
                    )}
                    {self && <span className="text-muted-foreground">You</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
