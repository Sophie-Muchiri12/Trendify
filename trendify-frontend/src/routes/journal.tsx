import { createFileRoute } from "@tanstack/react-router";
import journal from "@/assets/journal.jpg";
import vase from "@/assets/p-vase.jpg";
import sneaker from "@/assets/p-sneaker1.jpg";

export const Route = createFileRoute("/journal")({
  head: () => ({
    meta: [
      { title: "Journal — Trendify" },
      { name: "description", content: "Stories about makers, materials and moving well." },
      { property: "og:title", content: "Journal — Trendify" },
      { property: "og:description", content: "Stories about makers, materials and moving well." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Journal,
});

const posts = [
  {
    img: journal,
    tag: "Community",
    title: "Honoring the makers",
    text: "A visit to the weaving studio behind our indigo throws.",
  },
  {
    img: vase,
    tag: "Craft",
    title: "The beauty of raw clay",
    text: "Why we leave our terracotta unglazed.",
  },
  {
    img: sneaker,
    tag: "Movement",
    title: "10,000 steps, softly",
    text: "How Cloud Foam keeps city walks comfortable.",
  },
];

function Journal() {
  return (
    <div className="mx-auto max-w-7xl px-5 pt-10">
      <h1 className="text-5xl">Journal</h1>
      <div className="mt-8 grid gap-6 md:grid-cols-3">
        {posts.map((p) => (
          <article key={p.title} className="overflow-hidden rounded-3xl border bg-card">
            <img
              src={p.img}
              alt={p.title}
              loading="lazy"
              className="aspect-[4/3] w-full object-cover"
            />
            <div className="space-y-2 p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-terracotta">{p.tag}</p>
              <h2 className="text-2xl">{p.title}</h2>
              <p className="text-sm text-muted-foreground">{p.text}</p>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
