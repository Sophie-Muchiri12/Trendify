import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { Heart, Minus, Plus, Star, Truck, RotateCcw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { fetchProducts, formatPrice } from "@/lib/products";
import { useCart } from "@/lib/cart";
import { ProductCard } from "@/components/ProductCard";
import { Reviews } from "@/components/Reviews";

export const Route = createFileRoute("/product/$id")({
  loader: async ({ params }) => {
    const products = await fetchProducts();
    const product = products.find((p) => p.id === params.id);
    if (!product) throw notFound();
    const related = products
      .filter((p) => p.id !== product.id)
      .sort(
        (a, b) => Number(b.category === product.category) - Number(a.category === product.category),
      )
      .slice(0, 4);
    return { product, related };
  },
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: `${loaderData.product.name} — Trendify` },
          { name: "description", content: loaderData.product.description },
          { property: "og:title", content: `${loaderData.product.name} — Trendify` },
          { property: "og:description", content: loaderData.product.description },
          { property: "og:type", content: "product" },
          { name: "twitter:card", content: "summary_large_image" },
        ]
      : [
          { title: "Product not found — Trendify" },
          { name: "description", content: "This product could not be found at Trendify." },
          { property: "og:title", content: "Product not found — Trendify" },
          { property: "og:description", content: "This product could not be found at Trendify." },
          { property: "og:type", content: "website" },
          { name: "twitter:card", content: "summary_large_image" },
          { name: "robots", content: "noindex" },
        ],
  }),
  notFoundComponent: () => (
    <div className="py-32 text-center">
      <h1 className="text-4xl">Product not found</h1>
      <Link to="/shop" className="mt-4 inline-block underline">
        Back to shop
      </Link>
    </div>
  ),
  component: ProductPage,
});

function ProductPage() {
  const { product, related } = Route.useLoaderData();
  const { add, wishlist, toggleWish } = useCart();
  const [size, setSize] = useState<string | undefined>(product.sizes?.[2]);
  const [qty, setQty] = useState(1);

  return (
    <div className="mx-auto max-w-7xl px-5 pt-10">
      <Link to="/shop" className="text-sm text-muted-foreground">
        ← Back to shop
      </Link>
      <div className="mt-6 grid gap-10 md:grid-cols-2">
        <div className="arch overflow-hidden bg-muted">
          <img
            src={product.image}
            alt={product.name}
            width={816}
            height={816}
            className="aspect-square w-full object-cover"
          />
        </div>
        <div className="space-y-6 self-center">
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {product.category}
          </p>
          <h1 className="text-5xl">{product.name}</h1>
          <div className="flex items-center gap-4">
            <span className="text-2xl font-bold">{formatPrice(product.price)}</span>
            {product.oldPrice && (
              <span className="text-muted-foreground line-through">
                {formatPrice(product.oldPrice)}
              </span>
            )}
            <span className="flex items-center gap-1 text-sm">
              <Star className="h-4 w-4 fill-ochre text-ochre" />
              {product.rating}
              {product.reviewCount > 0 && (
                <span className="text-muted-foreground">({product.reviewCount})</span>
              )}
            </span>
          </div>
          <p className="text-muted-foreground">{product.description}</p>
          {product.sizes && (
            <div>
              <p className="mb-2 text-sm font-semibold">Size</p>
              <div className="flex flex-wrap gap-2">
                {product.sizes.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSize(s)}
                    className={`h-11 min-w-11 rounded-full border px-3 text-sm ${size === s ? "border-primary bg-primary text-primary-foreground" : "bg-card"}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center rounded-full border bg-card">
              <button
                aria-label="Decrease"
                className="p-3"
                onClick={() => setQty(Math.max(1, qty - 1))}
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center">{qty}</span>
              <button
                aria-label="Increase"
                className="p-3"
                onClick={() => setQty(Math.min(qty + 1, 10, Math.max(product.stock, 1)))}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <button
              disabled={product.stock === 0}
              onClick={() => {
                add(product.id, size, Math.min(qty, product.stock));
                toast.success(`${product.name} added to cart`);
              }}
              className="flex-1 rounded-full bg-terracotta px-8 py-3 font-semibold text-terracotta-foreground disabled:opacity-50"
            >
              {product.stock === 0 ? "Sold out" : "Add to cart"}
            </button>
            <button
              aria-label="Wishlist"
              onClick={() => toggleWish(product.id)}
              className="rounded-full border bg-card p-3"
            >
              <Heart
                className={`h-5 w-5 ${wishlist.includes(product.id) ? "fill-terracotta text-terracotta" : ""}`}
              />
            </button>
          </div>
          <div className="grid gap-3 rounded-2xl bg-secondary p-4 text-sm">
            <p className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-terracotta" /> Free delivery on orders over $100
            </p>
            <p className="flex items-center gap-2">
              <RotateCcw className="h-4 w-4 text-terracotta" /> 30-day free returns
            </p>
          </div>
        </div>
      </div>
      <Reviews slug={product.id} />
      <h2 className="mb-6 mt-20 text-3xl">You may also like</h2>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {related.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  );
}
