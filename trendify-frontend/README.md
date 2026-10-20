# Trendify — Frontend

Storefront for Trendify (sneakers, apparel and handmade home goods), built with
React 19, Vite, TanStack Router and Tailwind CSS v4. Products (and their images)
come from the Flask API in `../server`; the cart and wishlist are kept in
`localStorage`.

## Getting started

Start the backend first (see the root README), then:

```bash
npm install
npm run dev       # http://localhost:5173
```

In dev, Vite proxies `/api/*` and `/static/*` to the Flask server on
`http://127.0.0.1:5000` (see `vite.config.ts`). To point a build at a different API,
set `VITE_API_URL` (for example `VITE_API_URL=https://api.example.com`).

## Scripts

| Command           | What it does                       |
| ----------------- | ---------------------------------- |
| `npm run dev`     | Start the dev server               |
| `npm run build`   | Type-check and build to `dist/`    |
| `npm run preview` | Serve the production build locally |
| `npm run lint`    | Lint with ESLint + Prettier        |
| `npm run format`  | Format all files with Prettier     |
| `npm test`        | Run the tests with Vitest          |

## Project structure

```
index.html            HTML entry (meta tags, fonts, favicon)
src/
  main.tsx            Mounts the app
  router.tsx          Router setup
  routes/             One file per page (file-based routing)
    __root.tsx        Layout: header, footer, cart provider, toasts
    index.tsx         /
    shop.tsx          /shop
    product.$id.tsx   /product/:id
    cart.tsx          /cart
    about.tsx         /about
    journal.tsx       /journal
  components/         Shared components (header/footer, product card)
  lib/                Cart context, API client for products, helpers
  assets/             Product and page images
  styles.css          Tailwind setup and theme colours
```

`src/routeTree.gen.ts` is generated automatically from `src/routes/` when the dev
server, build or tests run. Don't edit it by hand.

## Deploying

`npm run build` outputs a static site to `dist/`, which you can host on Netlify,
Vercel, Cloudflare Pages, GitHub Pages or any static host. Because this is a
single-page app, configure the host to serve `index.html` for every path, so
links like `/product/123` work when opened directly or refreshed.
