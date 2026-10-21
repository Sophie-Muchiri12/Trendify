import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button, Card, Field, FormError, Page, RequireAuth } from "@/components/Forms";
import { fieldError } from "@/lib/forms";
import { ApiError, api, idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";
import { goToPayment, type Order } from "@/lib/orders";
import { fetchProducts, formatPrice, invalidateProducts } from "@/lib/products";

export const Route = createFileRoute("/checkout/")({
  loader: () => fetchProducts(),
  head: () => ({ meta: [{ title: "Checkout — Trendify" }] }),
  component: () => (
    <RequireAuth>
      <CheckoutPage />
    </RequireAuth>
  ),
});

function CheckoutPage() {
  const products = Route.useLoaderData();
  const { user } = useAuth();
  const { items, clear } = useCart();
  const navigate = useNavigate();
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState(user?.phone_number ?? "");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  // One key per checkout: retries and double-clicks reuse it, so only one order is created.
  const [key] = useState(idempotencyKey);

  const lines = items.flatMap((i) => {
    const p = products.find((x) => x.id === i.id);
    return p ? [{ ...i, p }] : [];
  });
  // Shown for convenience only; the server recalculates every price.
  const estimate = lines.reduce((s, l) => s + l.p.price * l.qty, 0);

  if (!user) return null;
  if (lines.length === 0)
    return (
      <Page title="Checkout" narrow>
        <Card>
          <p>Your cart is empty.</p>
          <Link to="/shop" className="mt-4 inline-block underline">
            Continue shopping
          </Link>
        </Card>
      </Page>
    );

  async function placeOrder(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api<{ order: Order; payment_url: string | null; payment_error?: string }>(
        "/orders",
        {
          method: "POST",
          headers: { "Idempotency-Key": key },
          body: {
            items: lines.map((l) => ({
              slug: l.id,
              quantity: l.qty,
              ...(l.size ? { size: l.size } : {}),
            })),
            shipping_address: address,
            phone_number: phone,
          },
        },
      );
      clear();
      invalidateProducts();
      if (res.payment_url) {
        goToPayment(res.payment_url, (p) => void navigate({ to: p }));
      } else {
        if (res.payment_error) toast.error(res.payment_error);
        void navigate({ to: "/account/orders/$ref", params: { ref: res.order.reference } });
      }
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  return (
    <Page title="Checkout">
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <Card>
          {!user.email_verified ? (
            <div>
              <h2 className="text-2xl">Verify your email first</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Check your inbox for the verification link, or request a new one from your account.
              </p>
              <Link to="/account" className="mt-4 inline-block underline">
                Go to your account
              </Link>
            </div>
          ) : (
            <form onSubmit={placeOrder} className="space-y-4">
              <h2 className="text-2xl">Delivery details</h2>
              <FormError error={error} />
              {error instanceof ApiError && error.status === 409 && (
                <p className="text-sm">
                  <Link to="/cart" className="underline">
                    Update your cart
                  </Link>{" "}
                  and try again.
                </p>
              )}
              <Field
                label="Delivery address"
                name="shipping_address"
                autoComplete="street-address"
                required
                minLength={5}
                maxLength={255}
                placeholder="Street, building, town"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                error={fieldError(error, "shipping_address")}
              />
              <Field
                label="Phone number for delivery"
                name="phone_number"
                type="tel"
                autoComplete="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                error={fieldError(error, "phone_number")}
              />
              <p className="text-xs text-muted-foreground">
                You'll pay securely on Pesapal by card or mobile money (M-Pesa, Airtel Money).
                Trendify never sees or stores your card details.
              </p>
              <Button type="submit" variant="accent" busy={busy} className="w-full">
                Place order and pay
              </Button>
            </form>
          )}
        </Card>
        <aside className="h-fit space-y-3 rounded-3xl bg-secondary p-6">
          <h2 className="text-2xl">Your order</h2>
          {lines.map((l) => (
            <div key={l.id + l.size} className="flex justify-between gap-2 text-sm">
              <span>
                {l.qty} × {l.p.name}
                {l.size && ` (${l.size})`}
              </span>
              <span>{formatPrice(l.p.price * l.qty)}</span>
            </div>
          ))}
          <div className="flex justify-between border-t pt-3 font-bold">
            <span>Total</span>
            <span>{formatPrice(estimate)}</span>
          </div>
        </aside>
      </div>
    </Page>
  );
}
