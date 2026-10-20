import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { FormError } from "@/components/Forms";
import { query, useAdminList } from "@/lib/admin";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/orders";

interface AdminReview {
  review_id: number;
  rating: number;
  review_text: string | null;
  status: "pending" | "approved" | "rejected";
  product_slug: string | null;
  product_name: string | null;
  user_email: string | null;
  created_at: string | null;
}

export const Route = createFileRoute("/admin/reviews")({ component: AdminReviews });

function AdminReviews() {
  const [status, setStatus] = useState("pending");
  const { data, error, reload } = useAdminList<AdminReview>(
    `/admin/reviews${query({ status: status || undefined })}`,
  );

  async function act(r: AdminReview, action: "approved" | "rejected" | "delete") {
    try {
      if (action === "delete") await api(`/admin/reviews/${r.review_id}`, { method: "DELETE" });
      else
        await api(`/admin/reviews/${r.review_id}`, { method: "PATCH", body: { status: action } });
      toast.success(action === "delete" ? "Review deleted" : `Review ${action}`);
      reload();
    } catch (err) {
      toast.error((err as Error).message);
    }
  }

  return (
    <div className="space-y-4">
      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        aria-label="Status"
        className="rounded-full border bg-card px-4 py-2 text-sm"
      >
        <option value="pending">Waiting for moderation</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
        <option value="">All</option>
      </select>
      <FormError error={error} />
      {data?.items.length === 0 && <p className="text-muted-foreground">Nothing here.</p>}
      <div className="space-y-3">
        {data?.items.map((r) => (
          <article key={r.review_id} className="rounded-3xl border bg-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
              <span>
                {r.product_slug ? (
                  <Link
                    to="/product/$id"
                    params={{ id: r.product_slug }}
                    className="font-semibold underline"
                  >
                    {r.product_name}
                  </Link>
                ) : (
                  r.product_name
                )}{" "}
                · {"★".repeat(r.rating)}
                {"☆".repeat(5 - r.rating)}
              </span>
              <span className="text-muted-foreground">
                {r.user_email} · {formatDate(r.created_at)} ·{" "}
                <span className="capitalize">{r.status}</span>
              </span>
            </div>
            {/* Rendered as text by React: any HTML in a review is shown, never executed. */}
            {r.review_text && <p className="mt-3 whitespace-pre-line text-sm">{r.review_text}</p>}
            <div className="mt-4 flex gap-4 text-sm">
              {r.status !== "approved" && (
                <button className="underline" onClick={() => void act(r, "approved")}>
                  Approve
                </button>
              )}
              {r.status !== "rejected" && (
                <button className="underline" onClick={() => void act(r, "rejected")}>
                  Reject
                </button>
              )}
              <button className="text-destructive underline" onClick={() => void act(r, "delete")}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
