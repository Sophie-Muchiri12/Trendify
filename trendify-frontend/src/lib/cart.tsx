import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export interface CartItem {
  id: string;
  size?: string | undefined;
  qty: number;
}

interface Ctx {
  items: CartItem[];
  wishlist: string[];
  add: (id: string, size?: string, qty?: number) => void;
  setQty: (id: string, size: string | undefined, qty: number) => void;
  remove: (id: string, size?: string) => void;
  clear: () => void;
  toggleWish: (id: string) => void;
  count: number;
}

const CartContext = createContext<Ctx | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      setItems(JSON.parse(localStorage.getItem("cart") || "[]"));
      setWishlist(JSON.parse(localStorage.getItem("wishlist") || "[]"));
    } catch {
      /* ignore */
    }
    setLoaded(true);
  }, []);
  useEffect(() => {
    if (loaded) localStorage.setItem("cart", JSON.stringify(items));
  }, [items, loaded]);
  useEffect(() => {
    if (loaded) localStorage.setItem("wishlist", JSON.stringify(wishlist));
  }, [wishlist, loaded]);

  const same = (a: CartItem, id: string, size?: string) => a.id === id && a.size === size;

  const value: Ctx = {
    items,
    wishlist,
    count: items.reduce((s, i) => s + i.qty, 0),
    add: (id, size, qty = 1) =>
      setItems((prev) =>
        prev.some((i) => same(i, id, size))
          ? prev.map((i) => (same(i, id, size) ? { ...i, qty: i.qty + qty } : i))
          : [...prev, { id, size, qty }],
      ),
    setQty: (id, size, qty) =>
      setItems((prev) =>
        prev.map((i) => (same(i, id, size) ? { ...i, qty: Math.max(1, qty) } : i)),
      ),
    remove: (id, size) => setItems((prev) => prev.filter((i) => !same(i, id, size))),
    clear: () => setItems([]),
    toggleWish: (id) =>
      setWishlist((w) => (w.includes(id) ? w.filter((x) => x !== id) : [...w, id])),
  };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const c = useContext(CartContext);
  if (!c) throw new Error("useCart must be inside CartProvider");
  return c;
}
