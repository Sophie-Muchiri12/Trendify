import { createFileRoute } from "@tanstack/react-router";
import hero from "@/assets/hero.jpg";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — Trendify" },
      { name: "description", content: "Our story: comfortable movement meets handmade craft." },
      { property: "og:title", content: "About — Trendify" },
      {
        property: "og:description",
        content: "Our story: comfortable movement meets handmade craft.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 pt-10 md:grid-cols-2">
      <div className="space-y-5">
        <h1 className="text-5xl">Where movement meets craft</h1>
        <p className="text-muted-foreground">
          Trendify began with a simple idea: the things you wear and live with should feel good,
          last long and carry a story. We pair performance sneakers with linen apparel and home
          goods made by small studios.
        </p>
        <p className="text-muted-foreground">
          Every product is chosen for comfort, honest materials and the hands that made it.
        </p>
      </div>
      <img
        src={hero}
        alt="Our style"
        width={1536}
        height={1024}
        className="arch aspect-[4/5] w-full object-cover"
      />
    </div>
  ),
});
