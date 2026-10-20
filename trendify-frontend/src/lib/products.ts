import { api } from "@/lib/api";

export type Category = "Footwear" | "Apparel" | "Ceramics" | "Home";

export interface Product {
  id: string;
  productId: number;
  name: string;
  category: Category;
  price: number;
  oldPrice?: number | undefined;
  rating: number;
  reviewCount: number;
  image: string;
  badge?: string | undefined;
  sizes?: string[] | undefined;
  description: string;
  stock: number;
}

/** Shape returned by the Flask API (server/models/product.py → to_dict). */
export interface ApiProduct {
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
  review_count: number;
  badge: string | null;
  sizes: string[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export const categories: Category[] = ["Footwear", "Apparel", "Ceramics", "Home"];

export const toProduct = (p: ApiProduct): Product => ({
  id: p.slug,
  productId: p.product_id,
  name: p.name,
  category: p.category,
  price: p.price,
  oldPrice: p.old_price ?? undefined,
  rating: p.rating ?? 0,
  reviewCount: p.review_count,
  image: p.image_url ?? "",
  badge: p.badge ?? undefined,
  sizes: p.sizes.length ? p.sizes : undefined,
  description: p.description,
  stock: p.stock_quantity,
});

export type ProductQuery = {
  q?: string | undefined;
  category?: Category | undefined;
  sort?: "featured" | "price_asc" | "price_desc" | "rating" | "newest" | undefined;
};

/** Search the catalog on the server. */
export async function searchProducts(query: ProductQuery = {}): Promise<Product[]> {
  const params = new URLSearchParams({ per_page: "100" });
  for (const [k, v] of Object.entries(query)) if (v) params.set(k, v);
  const page = await api<Page<ApiProduct>>(`/products?${params}`);
  return page.items.map(toProduct);
}

let cache: Promise<Product[]> | undefined;

/** All products, fetched once and shared by every page. */
export function fetchProducts(): Promise<Product[]> {
  cache ??= searchProducts().catch((err: unknown) => {
    cache = undefined; // let the next navigation retry
    throw err;
  });
  return cache;
}

/** Forget cached products (after an admin edit or an order changes stock). */
export function invalidateProducts() {
  cache = undefined;
}

export const formatPrice = (n: number) => `$${n.toFixed(n % 1 === 0 ? 0 : 2)}`;
