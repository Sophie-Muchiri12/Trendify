import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { categories, fetchProducts, type Category } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";

type Search = { category?: Category | undefined; q?: string | undefined };

export const Route = createFileRoute("/shop")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    category: categories.includes(s["category"] as Category)
      ? (s["category"] as Category)
      : undefined,
    q: typeof s["q"] === "string" && s["q"] ? s["q"] : undefined,
  }),
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
  loader: () => fetchProducts(),
  component: Shop,
});

function Shop() {
  const { category, q } = Route.useSearch();
  const products = Route.useLoaderData();
  const [sort, setSort] = useState("featured");
  const [text, setText] = useState(q ?? "");
  const list = useMemo(() => {
    let l = products.filter(
      (p) =>
        (!category || p.category === category) && p.name.toLowerCase().includes(text.toLowerCase()),
    );
    if (sort === "low") l = [...l].sort((a, b) => a.price - b.price);
    if (sort === "high") l = [...l].sort((a, b) => b.price - a.price);
    return l;
  }, [products, category, text, sort]);

  return (
    <div className="mx-auto max-w-7xl px-5 pt-10">
      <h1 className="text-5xl">{category ?? "Shop all"}</h1>
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <Link
          to="/shop"
          search={{ q: undefined, category: undefined }}
          className={`rounded-full border px-4 py-2 text-sm ${!category ? "bg-primary text-primary-foreground" : "bg-card"}`}
        >
          All
        </Link>
        {categories.map((c) => (
          <Link
            key={c}
            to="/shop"
            search={{ category: c, q: undefined }}
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
            className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
          />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-full border bg-card px-4 py-2 text-sm"
          >
            <option value="featured">Featured</option>
            <option value="low">Price: low to high</option>
            <option value="high">Price: high to low</option>
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
