import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import {
  ArrowRight,
  Search,
  Truck,
  Footprints,
  ShieldCheck,
  Feather,
  Wind,
  Leaf,
  Hand,
  Sparkles,
  Star,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import hero from "@/assets/hero-grey.jpg";
import journal from "@/assets/journal.jpg";
import { categories, fetchProducts } from "@/lib/products";
import { ProductCard } from "@/components/ProductCard";
import sneaker1 from "@/assets/p-sneaker1.jpg";
import shirt from "@/assets/p-shirt.jpg";
import vase from "@/assets/p-vase.jpg";
import lamp from "@/assets/p-lamp.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Trendify — Move well, live artfully" },
      {
        name: "description",
        content: "Comfortable sneakers, linen apparel and handmade ceramics and home goods.",
      },
      { property: "og:title", content: "Trendify — Move well, live artfully" },
      {
        property: "og:description",
        content: "Comfortable sneakers, linen apparel and handmade home goods.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  loader: async () => [...(await fetchProducts())].sort((a, b) => b.rating - a.rating).slice(0, 6),
  component: Index,
});

const collections = [
  {
    name: "Footwear",
    text: "Cushioned comfort for every city step.",
    img: sneaker1,
    bg: "bg-plum",
  },
  { name: "Apparel", text: "Breathable linen in earthy tones.", img: shirt, bg: "bg-terracotta" },
  { name: "Ceramics", text: "Hand-thrown pieces with character.", img: vase, bg: "bg-indigo" },
  { name: "Home", text: "Warm objects for slow living.", img: lamp, bg: "bg-ochre" },
] as const;

const features = [
  { icon: Feather, t: "Cloud Foam", s: "Featherlight cushioning" },
  { icon: Wind, t: "Breath Tech", s: "Airflow in any weather" },
  { icon: Footprints, t: "Grip Control", s: "Sure footing on any surface" },
  { icon: Hand, t: "Handmade", s: "Crafted by local makers" },
  { icon: Sparkles, t: "Natural Dyes", s: "Indigo, rust and clay" },
  { icon: Leaf, t: "Eco Materials", s: "Kinder to the planet" },
];

function Index() {
  const bestSellers = Route.useLoaderData();
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  return (
    <div className="mx-auto max-w-7xl space-y-20 px-5 pt-6">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-[2.5rem] bg-secondary">
        <img
          src={hero}
          alt="Woman walking in linen and sneakers"
          width={1920}
          height={800}
          className="absolute inset-0 h-full w-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-secondary/90 via-secondary/30 to-transparent" />
        <div className="relative grid min-h-[560px] items-center gap-6 p-8 md:grid-cols-[1.2fr_1fr] md:p-14">
          <div className="max-w-xl space-y-6">
            <span className="inline-block rounded-full bg-card px-4 py-1.5 text-xs font-semibold uppercase tracking-wider">
              Autumn collection
            </span>
            <h1 className="text-5xl leading-[1.02] md:text-7xl">
              Move well,
              <br />
              <em className="text-terracotta">live artfully.</em>
            </h1>
            <p className="text-muted-foreground">
              Comfortable sneakers, breathable linen and handmade goods — chosen for the rhythm of
              your day.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                to="/shop"
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
              >
                Explore the shop <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/journal" className="rounded-full bg-card px-6 py-3 text-sm font-semibold">
                Read the journal
              </Link>
            </div>
          </div>
          <div className="hidden flex-col items-end gap-3 md:flex">
            {[
              { i: Truck, t: "Free delivery", s: "over $100" },
              { i: Footprints, t: "Try before you buy", s: "free at-home try-on" },
              { i: ShieldCheck, t: "Authentic goods", s: "quality guaranteed" },
            ].map((b) => (
              <div
                key={b.t}
                className="flex w-56 items-center gap-3 rounded-2xl bg-card/90 p-4 shadow-soft backdrop-blur"
              >
                <b.i className="h-5 w-5 text-terracotta" />
                <div>
                  <p className="text-sm font-semibold">{b.t}</p>
                  <p className="text-xs text-muted-foreground">{b.s}</p>
                </div>
              </div>
            ))}
            <div className="mt-6 flex items-center gap-3 rounded-full bg-card/90 px-4 py-2 shadow-soft">
              <div className="flex -space-x-2">
                {["bg-terracotta", "bg-primary", "bg-indigo"].map((c) => (
                  <span key={c} className={`h-7 w-7 rounded-full border-2 border-card ${c}`} />
                ))}
              </div>
              <div className="text-xs">
                <p className="font-semibold">10,000+ customers</p>
                <p className="flex items-center gap-1">
                  4.9 <Star className="h-3 w-3 fill-ochre text-ochre" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Search + chips */}
      <section className="-mt-12 flex flex-col gap-4 lg:flex-row">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            navigate({ to: "/shop", search: { q, category: undefined } });
          }}
          className="flex flex-1 items-center rounded-full border bg-card p-1.5 pl-5 shadow-soft"
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search sneakers, linen, ceramics…"
            className="flex-1 bg-transparent text-sm outline-none"
          />
          <button
            aria-label="Search"
            className="rounded-full bg-primary p-3 text-primary-foreground"
          >
            <Search className="h-4 w-4" />
          </button>
        </form>
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <Link
              key={c}
              to="/shop"
              search={{ category: c, q: undefined }}
              className="rounded-full border bg-card px-5 py-3 text-sm font-medium hover:border-terracotta"
            >
              {c}
            </Link>
          ))}
        </div>
      </section>

      {/* Best sellers */}
      <section>
        <div className="mb-6 flex items-end justify-between">
          <h2 className="text-3xl md:text-4xl">Best sellers</h2>
          <Link to="/shop" className="flex items-center gap-1 text-sm font-semibold">
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {bestSellers.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>

      {/* Collections */}
      <section className="relative">
        <div className="absolute -left-32 top-10 -z-10 h-80 w-80 rounded-full bg-terracotta/20 blur-2xl" />
        <h2 className="mb-8 text-center text-3xl md:text-4xl">The collections</h2>
        <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
          {collections.map((c) => (
            <Link
              key={c.name}
              to="/shop"
              search={{ category: c.name, q: undefined }}
              className={`group overflow-hidden rounded-[2rem] ${c.bg} text-terracotta-foreground`}
            >
              <div className="arch m-3 overflow-hidden bg-card">
                <img
                  src={c.img}
                  alt={c.name}
                  loading="lazy"
                  width={816}
                  height={816}
                  className="aspect-[4/3] w-full object-cover transition duration-500 group-hover:scale-105"
                />
              </div>
              <div className="space-y-2 p-5 pt-2">
                <h3 className="text-2xl">{c.name}</h3>
                <p className="text-sm opacity-80">{c.text}</p>
                <span className="inline-block border-b text-xs font-semibold uppercase tracking-wider">
                  Shop now
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Features */}
      <section>
        <h2 className="mb-6 text-3xl md:text-4xl">Made for movement &amp; living</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {features.map((f) => (
            <div key={f.t} className="rounded-3xl border bg-card p-6 text-center">
              <f.icon className="mx-auto h-8 w-8 text-primary" strokeWidth={1.4} />
              <p className="mt-4 text-sm font-bold uppercase tracking-wider">{f.t}</p>
              <p className="mt-1 text-xs text-muted-foreground">{f.s}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Journal */}
      <section>
        <h2 className="mb-8 text-center text-3xl md:text-4xl">Journal stories</h2>
        <div className="grid overflow-hidden rounded-[2rem] bg-terracotta text-terracotta-foreground md:grid-cols-2">
          <img
            src={journal}
            alt="Artisan weaving on a loom"
            loading="lazy"
            width={1280}
            height={800}
            className="h-full min-h-72 w-full object-cover"
          />
          <div className="flex flex-col justify-center gap-4 p-10">
            <p className="text-xs uppercase tracking-[0.3em] opacity-80">Design &amp; community</p>
            <h3 className="text-3xl md:text-4xl">Honoring the makers</h3>
            <p className="opacity-85">
              Meet the weavers and potters behind our home collection, and the slow craft that
              shapes every piece.
            </p>
            <Link to="/journal" className="w-fit border-b font-semibold">
              + Read more
            </Link>
          </div>
        </div>
      </section>

      {/* Club */}
      <section className="flex flex-col items-center gap-6 rounded-[2rem] bg-secondary p-10 md:flex-row md:justify-between">
        <div className="space-y-2">
          <h2 className="text-3xl">Join the Trendify Club</h2>
          <p className="text-sm text-muted-foreground">
            5% cashback on every order, early access to new drops and members-only gifts.
          </p>
        </div>
        <button
          onClick={() => toast.success("Welcome to the club!")}
          className="rounded-full bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground"
        >
          Become a member
        </button>
      </section>
    </div>
  );
}
