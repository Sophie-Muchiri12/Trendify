import { Link } from "@tanstack/react-router";
import {
  Instagram,
  Facebook,
  Menu,
  ShoppingBag,
  User,
  X,
  Truck,
  RotateCcw,
  ShieldCheck,
  Headphones,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useCart } from "@/lib/cart";

const nav = [
  { to: "/shop", label: "Shop all" },
  { to: "/journal", label: "Journal" },
  { to: "/about", label: "About" },
] as const;

function Logo() {
  return (
    <Link to="/" className="leading-none">
      <span className="font-display text-2xl font-semibold tracking-tight">Trendify</span>
      <span className="block text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
        Move · Live · Make
      </span>
    </Link>
  );
}

export function SiteHeader() {
  const { count } = useCart();
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <Logo />
        <nav className="hidden gap-8 text-sm font-medium md:flex">
          {nav.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className="hover:opacity-60"
              activeProps={{ className: "underline underline-offset-8 decoration-2" }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <button
            className="hidden items-center gap-2 rounded-full border px-4 py-2 text-sm sm:flex"
            onClick={() => toast("Accounts coming soon")}
          >
            <User className="h-4 w-4" /> Sign in
          </button>
          <Link
            to="/cart"
            className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
          >
            <ShoppingBag className="h-4 w-4" /> <span className="hidden sm:inline">Cart</span>
            <span className="grid h-5 min-w-5 place-items-center rounded-full bg-primary-foreground px-1 text-xs font-bold text-primary">
              {count}
            </span>
          </Link>
          <button className="md:hidden" aria-label="Menu" onClick={() => setOpen(!open)}>
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>
      {open && (
        <nav className="flex flex-col gap-4 border-t px-5 py-4 md:hidden">
          {nav.map((n) => (
            <Link key={n.to} to={n.to} onClick={() => setOpen(false)}>
              {n.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

export function SiteFooter() {
  const perks = [
    { icon: Truck, t: "Free delivery", s: "on orders over $100" },
    { icon: RotateCcw, t: "30-day returns", s: "no questions asked" },
    { icon: ShieldCheck, t: "Authentic goods", s: "quality guaranteed" },
    { icon: Headphones, t: "Support 24/7", s: "we're always here" },
  ];
  return (
    <footer className="mt-20">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 border-y px-5 py-8 md:grid-cols-4">
        {perks.map((p) => (
          <div key={p.t} className="flex items-center gap-3">
            <p.icon className="h-6 w-6 text-terracotta" />
            <div>
              <p className="text-sm font-semibold">{p.t}</p>
              <p className="text-xs text-muted-foreground">{p.s}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="bg-ink text-ink-foreground">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 md:grid-cols-4">
          <div className="space-y-3">
            <p className="font-display text-2xl">Trendify</p>
            <p className="text-sm opacity-70">
              Sneakers, apparel and handmade goods for a life in motion.
            </p>
            <div className="flex gap-3 opacity-80">
              <Instagram className="h-5 w-5" />
              <Facebook className="h-5 w-5" />
            </div>
          </div>
          <div className="space-y-2 text-sm">
            <p className="font-semibold uppercase tracking-wider">Shop</p>
            <Link to="/shop" className="block opacity-70">
              All products
            </Link>
            <Link to="/cart" className="block opacity-70">
              Cart
            </Link>
          </div>
          <div className="space-y-2 text-sm">
            <p className="font-semibold uppercase tracking-wider">Company</p>
            <Link to="/about" className="block opacity-70">
              About
            </Link>
            <Link to="/journal" className="block opacity-70">
              Journal
            </Link>
          </div>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              toast.success("Thanks for subscribing!");
              (e.target as HTMLFormElement).reset();
            }}
          >
            <p className="text-sm font-semibold uppercase tracking-wider">Stay connected</p>
            <div className="flex overflow-hidden rounded-full bg-ink-foreground">
              <input
                required
                type="email"
                placeholder="Your email"
                className="min-w-0 flex-1 bg-transparent px-4 py-2 text-sm text-ink outline-none"
              />
              <button className="bg-terracotta px-4 text-xs font-semibold uppercase text-terracotta-foreground">
                Subscribe
              </button>
            </div>
          </form>
        </div>
        <p className="pb-6 text-center text-xs opacity-50">© 2026 Trendify. All rights reserved.</p>
      </div>
    </footer>
  );
}
