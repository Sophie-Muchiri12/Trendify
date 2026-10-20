export type Category = "Footwear" | "Apparel" | "Ceramics" | "Home";

export interface Product {
  id: string;
  name: string;
  category: Category;
  price: number;
  oldPrice?: number | undefined;
  rating: number;
  image: string;
  badge?: string | undefined;
  sizes?: string[] | undefined;
  description: string;
  stock: number;
}

/** Shape returned by the Flask API (server/models/product.py → to_dict). */
interface ApiProduct {
  product_id: number;
  slug: string;
  name: string;
  description: string;
  price: number;
  old_price: number | null;
  stock_quantity: number;
  category: Category;
  image_url: string | null;
  rating: number | null;
  badge: string | null;
  sizes: string[];
}

export const categories: Category[] = ["Footwear", "Apparel", "Ceramics", "Home"];

// In dev, Vite proxies /api and /static to the Flask server (see vite.config.ts).
const API_URL = import.meta.env["VITE_API_URL"] ?? "/api";

const toProduct = (p: ApiProduct): Product => ({
  id: p.slug,
  name: p.name,
  category: p.category,
  price: p.price,
  oldPrice: p.old_price ?? undefined,
  rating: p.rating ?? 0,
  image: p.image_url ?? "",
  badge: p.badge ?? undefined,
  sizes: p.sizes.length ? p.sizes : undefined,
  description: p.description,
  stock: p.stock_quantity,
});

let cache: Promise<Product[]> | undefined;

/** All products, fetched once and shared by every page. */
export function fetchProducts(): Promise<Product[]> {
  cache ??= fetch(`${API_URL}/products`)
    .then((res) => {
      if (!res.ok) throw new Error(`Could not load products (HTTP ${res.status})`);
      return res.json() as Promise<ApiProduct[]>;
    })
    .then((list) => list.filter((p) => p.slug).map(toProduct))
    .catch((err: unknown) => {
      cache = undefined; // let the next navigation retry
      throw err;
    });
  return cache;
}

export const formatPrice = (n: number) => `$${n.toFixed(0)}`;
