import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { categories, searchProducts, type Category, type ProductQuery } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";

const sorts = ["featured", "price_asc", "price_desc", "rating", "newest"] as const;
type Sort = (typeof sorts)[number];

type Search = { category?: Category | undefined; q?: string | undefined; sort?: Sort | undefined };

export const Route = createFileRoute("/shop")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    category: categories.includes(s["category"] as Category)
      ? (s["category"] as Category)
      : undefined,
    q: typeof s["q"] === "string" && s["q"] ? s["q"].slice(0, 100) : undefined,
    sort: sorts.includes(s["sort"] as Sort) ? (s["sort"] as Sort) : undefined,
  }),
  loaderDeps: ({ search }) => search,
  // Searching, filtering and sorting happen on the server (validated, parameterized queries).
  loader: ({ deps }) => searchProducts(deps as ProductQuery),
  head: () => ({
    meta: [
      { title: "Shop all — Trendify" },
      { name: "description", content: "Browse sneakers, linen apparel, ceramics and home goods." },
      { property: "og:title", content: "Shop all — Trendify" },
      {
        property: "og:description",
        content: "Browse sneakers, linen apparel, ceramics and home goods.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Shop,
});

function Shop() {
  const { category, q, sort } = Route.useSearch();
  const list = Route.useLoaderData();
  const navigate = useNavigate({ from: "/shop" });
  const [text, setText] = useState(q ?? "");

  // Update the URL (and so the server query) shortly after the user stops typing.
  useEffect(() => {
    const t = setTimeout(() => {
      if ((q ?? "") !== text.trim())
        void navigate({ search: (s) => ({ ...s, q: text.trim() || undefined }), replace: true });
    }, 300);
    return () => clearTimeout(t);
  }, [text, q, navigate]);

  return (
    <div className="mx-auto max-w-7xl px-5 pt-10">
      <h1 className="text-5xl">{category ?? "Shop all"}</h1>
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <Link
          to="/shop"
          search={(s) => ({ ...s, category: undefined })}
          className={`rounded-full border px-4 py-2 text-sm ${!category ? "bg-primary text-primary-foreground" : "bg-card"}`}
        >
          All
        </Link>
        {categories.map((c) => (
          <Link
            key={c}
            to="/shop"
            search={(s) => ({ ...s, category: c })}
            className={`rounded-full border px-4 py-2 text-sm ${category === c ? "bg-primary text-primary-foreground" : "bg-card"}`}
          >
            {c}
          </Link>
        ))}
        <div className="ml-auto flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Search…"
            maxLength={100}
            aria-label="Search products"
            className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
          />
          <select
            value={sort ?? "featured"}
            aria-label="Sort products"
            onChange={(e) =>
              void navigate({ search: (s) => ({ ...s, sort: e.target.value as Sort }) })
            }
            className="rounded-full border bg-card px-4 py-2 text-sm"
          >
            <option value="featured">Featured</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
            <option value="rating">Top rated</option>
            <option value="newest">Newest</option>
          </select>
        </div>
      </div>
      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        {list.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
      {list.length === 0 && (
        <p className="py-20 text-center text-muted-foreground">No products match your search.</p>
      )}
    </div>
  );
}
