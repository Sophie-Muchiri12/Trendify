import {
  Outlet,
  Link,
  createRootRoute,
  useRouter,
  HeadContent,
  type ErrorComponentProps,
} from "@tanstack/react-router";

import { AuthProvider } from "@/lib/auth";
import { CartProvider } from "@/lib/cart";
import { SiteHeader, SiteFooter } from "@/components/SiteChrome";
import { Toaster } from "@/components/ui/sonner";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  console.error(error);
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

// Static tags (charset, viewport, fonts, favicon) live in index.html; these are
// defaults that child routes override via their own head().
export const Route = createRootRoute({
  head: () => ({
    meta: [
      { title: "Trendify — Sneakers, apparel & handmade goods" },
      { name: "description", content: "Shop sneakers, linen apparel and handmade home goods." },
    ],
  }),
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootComponent() {
  return (
    <AuthProvider>
      <CartProvider>
        <HeadContent />
        <SiteHeader />
        <main>
          <Outlet />
        </main>
        <SiteFooter />
        <Toaster position="bottom-right" />
      </CartProvider>
    </AuthProvider>
  );
}
