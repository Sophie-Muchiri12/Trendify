import { Link } from "@tanstack/react-router";
import { Heart, Star } from "lucide-react";
import { toast } from "sonner";
import { formatPrice, type Product } from "@/lib/products";
import { useCart } from "@/lib/cart";

export function ProductCard({ product }: { product: Product }) {
  const { add, wishlist, toggleWish } = useCart();
  const wished = wishlist.includes(product.id);
  return (
    <div className="group relative flex flex-col rounded-3xl border bg-card p-3 transition hover:shadow-soft">
      {product.badge && (
        <span className="absolute left-5 top-5 z-10 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground">
          {product.badge}
        </span>
      )}
      <button
        aria-label="Add to wishlist"
        onClick={() => toggleWish(product.id)}
        className="absolute right-5 top-5 z-10 rounded-full bg-card/80 p-2 backdrop-blur"
      >
        <Heart
          className={`h-4 w-4 ${wished ? "fill-terracotta text-terracotta" : "text-foreground"}`}
        />
      </button>
      <Link
        to="/product/$id"
        params={{ id: product.id }}
        className="block overflow-hidden rounded-2xl bg-muted"
      >
        <img
          src={product.image}
          alt={product.name}
          loading="lazy"
          width={816}
          height={816}
          className="aspect-square w-full object-cover transition duration-500 group-hover:scale-105"
        />
      </Link>
      <div className="flex flex-1 flex-col px-1 pt-3">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">{product.category}</p>
        <Link to="/product/$id" params={{ id: product.id }} className="mt-1 font-semibold">
          {product.name}
        </Link>
        <div className="mt-2 flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            <span className="font-bold">{formatPrice(product.price)}</span>
            {product.oldPrice && (
              <span className="text-sm text-muted-foreground line-through">
                {formatPrice(product.oldPrice)}
              </span>
            )}
          </div>
          <span className="flex items-center gap-1 text-sm">
            <Star className="h-3.5 w-3.5 fill-ochre text-ochre" />
            {product.rating}
          </span>
        </div>
        <button
          onClick={() => {
            add(product.id, product.sizes?.[2]);
            toast.success(`${product.name} added to cart`);
          }}
          className="mt-3 rounded-full bg-terracotta px-4 py-2 text-xs font-semibold uppercase tracking-wider text-terracotta-foreground transition hover:opacity-90"
        >
          Add to cart
        </button>
      </div>
    </div>
  );
}
