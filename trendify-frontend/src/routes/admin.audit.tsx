import { createFileRoute } from "@tanstack/react-router";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Button, FormError } from "@/components/Forms";
import { query, useAdminList } from "@/lib/admin";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/orders";

interface AuditEntry {
  id: number;
  created_at: string;
  action: string;
  outcome: "success" | "failure" | "denied";
  actor_user_id: number | null;
  actor_email: string | null;
  ip_address: string | null;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown> | null;
}

export const Route = createFileRoute("/admin/audit")({ component: AuditLog });

function AuditLog() {
  const [action, setAction] = useState("");
  const [outcome, setOutcome] = useState("");
  const [page, setPage] = useState(1);
  const [check, setCheck] = useState<{
    ok: boolean;
    first_bad_id: number | null;
    checked: number;
  } | null>(null);
  const [checking, setChecking] = useState(false);
  const { data, error } = useAdminList<AuditEntry>(
    `/admin/audit-logs${query({ action: action.trim() || undefined, outcome: outcome || undefined, page })}`,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPage(1);
          }}
          placeholder="Action starts with… (e.g. auth.)"
          aria-label="Filter by action"
          maxLength={64}
          className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
        />
        <select
          value={outcome}
          onChange={(e) => {
            setOutcome(e.target.value);
            setPage(1);
          }}
          aria-label="Outcome"
          className="rounded-full border bg-card px-4 py-2 text-sm"
        >
          <option value="">All outcomes</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="denied">Denied</option>
        </select>
        <Button
          className="ml-auto"
          variant="outline"
          busy={checking}
          onClick={async () => {
            setChecking(true);
            try {
              setCheck(await api("/admin/audit-logs/verify"));
            } finally {
              setChecking(false);
            }
          }}
        >
          Verify integrity
        </Button>
      </div>
      {check && (
        <p
          className={`flex items-center gap-2 rounded-2xl px-4 py-3 text-sm ${check.ok ? "bg-green-600/10 text-green-800" : "bg-destructive/10 text-destructive"}`}
        >
          {check.ok ? <ShieldCheck className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
          {check.ok
            ? `All ${check.checked} entries are intact: the hash chain is unbroken.`
            : `The log has been modified: the hash chain breaks at entry #${check.first_bad_id}.`}
        </p>
      )}
      <FormError error={error} />
      <div className="overflow-x-auto rounded-3xl border bg-card">
        <table className="w-full text-sm">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="p-3">#</th>
              <th className="p-3">Time</th>
              <th className="p-3">Action</th>
              <th className="p-3">Outcome</th>
              <th className="p-3">Who</th>
              <th className="p-3">IP</th>
              <th className="p-3">Target</th>
              <th className="p-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((e) => (
              <tr key={e.id} className="border-t align-top">
                <td className="p-3 text-muted-foreground">{e.id}</td>
                <td className="whitespace-nowrap p-3">{formatDate(e.created_at)}</td>
                <td className="p-3 font-mono text-xs">{e.action}</td>
                <td
                  className={`p-3 ${e.outcome === "success" ? "" : "font-semibold text-destructive"}`}
                >
                  {e.outcome}
                </td>
                <td className="p-3">
                  {e.actor_email ?? (e.actor_user_id ? `#${e.actor_user_id}` : "—")}
                </td>
                <td className="p-3">{e.ip_address ?? "—"}</td>
                <td className="p-3">
                  {e.target_type ? `${e.target_type} ${e.target_id ?? ""}` : "—"}
                </td>
                <td className="max-w-xs break-words p-3 font-mono text-xs text-muted-foreground">
                  {e.details ? JSON.stringify(e.details) : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-4 text-sm">
          <button
            disabled={page <= 1}
            className="underline disabled:opacity-40"
            onClick={() => setPage(page - 1)}
          >
            Newer
          </button>
          <span>
            Page {data.page} of {data.pages}
          </span>
          <button
            disabled={page >= data.pages}
            className="underline disabled:opacity-40"
            onClick={() => setPage(page + 1)}
          >
            Older
          </button>
        </div>
      )}
    </div>
  );
}
