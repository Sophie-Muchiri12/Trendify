import { createFileRoute, Link } from "@tanstack/react-router";
import { Minus, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useCart } from "@/lib/cart";
import { fetchProducts, formatPrice } from "@/lib/products";

export const Route = createFileRoute("/cart")({
  head: () => ({
    meta: [
      { title: "Your cart — Trendify" },
      { name: "description", content: "Review the items in your cart." },
      { property: "og:title", content: "Your cart — Trendify" },
      { property: "og:description", content: "Review the items in your cart." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  loader: () => fetchProducts(),
  component: CartPage,
});

function CartPage() {
  const { items, setQty, remove, clear } = useCart();
  const products = Route.useLoaderData();
  const lines = items.flatMap((i) => {
    const p = products.find((x) => x.id === i.id);
    return p ? [{ ...i, p }] : [];
  });
  const subtotal = lines.reduce((s, l) => s + l.p.price * l.qty, 0);
  const shipping = subtotal === 0 || subtotal >= 100 ? 0 : 10;

  if (lines.length === 0)
    return (
      <div className="py-32 text-center">
        <h1 className="text-5xl">Your cart is empty</h1>
        <Link
          to="/shop"
          className="mt-6 inline-block rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
        >
          Start shopping
        </Link>
      </div>
    );

  return (
    <div className="mx-auto max-w-7xl px-5 pt-10">
      <h1 className="text-5xl">Your cart</h1>
      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4">
          {lines.map((l) => (
            <div
              key={l.id + l.size}
              className="flex items-center gap-4 rounded-3xl border bg-card p-3"
            >
              <img
                src={l.p.image}
                alt={l.p.name}
                width={96}
                height={96}
                className="h-24 w-24 rounded-2xl object-cover"
              />
              <div className="flex-1">
                <Link to="/product/$id" params={{ id: l.id }} className="font-semibold">
                  {l.p.name}
                </Link>
                {l.size && <p className="text-sm text-muted-foreground">Size {l.size}</p>}
                <p className="text-sm font-bold">{formatPrice(l.p.price)}</p>
              </div>
              <div className="flex items-center rounded-full border">
                <button
                  aria-label="Decrease"
                  className="p-2"
                  onClick={() => setQty(l.id, l.size, l.qty - 1)}
                >
                  <Minus className="h-4 w-4" />
                </button>
                <span className="w-6 text-center text-sm">{l.qty}</span>
                <button
                  aria-label="Increase"
                  className="p-2"
                  onClick={() => setQty(l.id, l.size, l.qty + 1)}
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              <button
                aria-label="Remove"
                onClick={() => remove(l.id, l.size)}
                className="p-2 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
        <aside className="h-fit space-y-3 rounded-3xl bg-secondary p-6">
          <h2 className="text-2xl">Summary</h2>
          <div className="flex justify-between text-sm">
            <span>Subtotal</span>
            <span>{formatPrice(subtotal)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Shipping</span>
            <span>{shipping ? formatPrice(shipping) : "Free"}</span>
          </div>
          <div className="flex justify-between border-t pt-3 font-bold">
            <span>Total</span>
            <span>{formatPrice(subtotal + shipping)}</span>
          </div>
          <button
            onClick={() => {
              clear();
              toast.success("Order placed! (demo)");
            }}
            className="w-full rounded-full bg-terracotta py-3 font-semibold text-terracotta-foreground"
          >
            Checkout
          </button>
        </aside>
      </div>
    </div>
  );
}
