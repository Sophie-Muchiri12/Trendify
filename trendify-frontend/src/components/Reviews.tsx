import { Link } from "@tanstack/react-router";
import { Star } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Button, FormError, TextArea, fieldError } from "@/components/Forms";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate } from "@/lib/orders";

interface PublicReview {
  review_id: number;
  rating: number;
  review_text: string | null;
  author: string;
  created_at: string | null;
}

interface OwnReview extends PublicReview {
  status: "pending" | "approved" | "rejected";
}

interface Eligibility {
  can_review: boolean;
  has_purchased: boolean;
  review: OwnReview | null;
}

function Stars({ value }: { value: number }) {
  return (
    <span className="flex" aria-label={`${value} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          className={`h-4 w-4 ${n <= value ? "fill-ochre text-ochre" : "text-muted-foreground"}`}
        />
      ))}
    </span>
  );
}

export function Reviews({ slug }: { slug: string }) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<PublicReview[]>([]);
  const [eligibility, setEligibility] = useState<Eligibility | null>(null);
  const [editing, setEditing] = useState(false);

  const load = useCallback(() => {
    api<{ items: PublicReview[] }>(`/products/${slug}/reviews`)
      .then((r) => setReviews(r.items))
      .catch(() => setReviews([]));
    if (user)
      api<Eligibility>(`/products/${slug}/reviews/eligibility`)
        .then(setEligibility)
        .catch(() => setEligibility(null));
    else setEligibility(null);
  }, [slug, user]);

  useEffect(load, [load]);

  const own = eligibility?.review;

  return (
    <section className="mt-20">
      <h2 className="mb-6 text-3xl">Reviews</h2>
      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          {reviews.length === 0 && <p className="text-muted-foreground">No reviews yet.</p>}
          {reviews.map((r) => (
            <article key={r.review_id} className="rounded-3xl border bg-card p-5">
              <div className="flex items-center justify-between">
                <Stars value={r.rating} />
                <span className="text-xs text-muted-foreground">{formatDate(r.created_at)}</span>
              </div>
              {/* React escapes this text, so review content can't inject HTML or scripts. */}
              {r.review_text && <p className="mt-3 whitespace-pre-line text-sm">{r.review_text}</p>}
              <p className="mt-3 text-xs font-semibold">{r.author} · Verified buyer</p>
            </article>
          ))}
        </div>
        <aside className="h-fit rounded-3xl bg-secondary p-6">
          {!user ? (
            <p className="text-sm">
              <Link to="/login" search={{ redirect: `/product/${slug}` }} className="underline">
                Sign in
              </Link>{" "}
              to review products you've bought.
            </p>
          ) : own && !editing ? (
            <div className="space-y-3 text-sm">
              <h3 className="text-xl">Your review</h3>
              <Stars value={own.rating} />
              {own.review_text && <p>{own.review_text}</p>}
              <p className="text-xs text-muted-foreground">
                Status: <span className="capitalize">{own.status}</span>
                {own.status === "pending" && " (it will appear once it's been checked)"}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setEditing(true)}>
                  Edit
                </Button>
                <Button
                  variant="danger"
                  onClick={async () => {
                    try {
                      await api(`/reviews/${own.review_id}`, { method: "DELETE" });
                      toast.success("Review deleted");
                      load();
                    } catch (err) {
                      toast.error((err as Error).message);
                    }
                  }}
                >
                  Delete
                </Button>
              </div>
            </div>
          ) : eligibility?.can_review || (own && editing) ? (
            <ReviewForm
              slug={slug}
              existing={own ?? null}
              onDone={() => {
                setEditing(false);
                load();
              }}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              {!user.email_verified
                ? "Verify your email to write reviews."
                : "You can review this product after you've bought it."}
            </p>
          )}
        </aside>
      </div>
    </section>
  );
}

function ReviewForm({
  slug,
  existing,
  onDone,
}: {
  slug: string;
  existing: OwnReview | null;
  onDone: () => void;
}) {
  const [rating, setRating] = useState(existing?.rating ?? 5);
  const [text, setText] = useState(existing?.review_text ?? "");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (existing)
        await api(`/reviews/${existing.review_id}`, {
          method: "PATCH",
          body: { rating, review_text: text },
        });
      else
        await api(`/products/${slug}/reviews`, {
          method: "POST",
          body: { rating, review_text: text },
        });
      toast.success("Thanks! Your review will appear once it's been checked.");
      onDone();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h3 className="text-xl">{existing ? "Edit your review" : "Write a review"}</h3>
      <FormError error={error} />
      <fieldset>
        <legend className="mb-2 text-sm font-semibold">Rating</legend>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              aria-label={`${n} star${n > 1 ? "s" : ""}`}
              aria-pressed={n === rating}
              onClick={() => setRating(n)}
            >
              <Star
                className={`h-7 w-7 ${n <= rating ? "fill-ochre text-ochre" : "text-muted-foreground"}`}
              />
            </button>
          ))}
        </div>
      </fieldset>
      <TextArea
        label="Your review (optional)"
        name="review_text"
        rows={4}
        maxLength={2000}
        value={text}
        onChange={(e) => setText(e.target.value)}
        error={fieldError(error, "review_text")}
      />
      <Button type="submit" busy={busy} className="w-full">
        {existing ? "Save changes" : "Submit review"}
      </Button>
    </form>
  );
}
