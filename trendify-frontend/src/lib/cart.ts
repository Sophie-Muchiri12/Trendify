import { createContext, useContext } from "react";

export interface CartItem {
  id: string;
  size?: string | undefined;
  qty: number;
}

export interface CartCtx {
  items: CartItem[];
  wishlist: string[];
  add: (id: string, size?: string, qty?: number) => void;
  setQty: (id: string, size: string | undefined, qty: number) => void;
  remove: (id: string, size?: string) => void;
  clear: () => void;
  toggleWish: (id: string) => void;
  count: number;
}

export const CartContext = createContext<CartCtx | null>(null);

export function useCart() {
  const c = useContext(CartContext);
  if (!c) throw new Error("useCart must be inside CartProvider");
  return c;
}
