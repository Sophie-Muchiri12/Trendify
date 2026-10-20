import path from "node:path";
import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";

/**
 * Content Security Policy for the built site (A02 / A04). Only our own scripts can run,
 * so injected markup can't execute JavaScript. Styles allow 'unsafe-inline' because the
 * toast library injects a <style> tag; scripts never do.
 */
function contentSecurityPolicy(apiOrigin: string) {
  const connect = ["'self'", apiOrigin].filter(Boolean).join(" ");
  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    `img-src 'self' data: ${apiOrigin}`.trim(),
    `connect-src ${connect}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests",
  ].join("; ");
}

// Headers for the dev/preview servers. In production, set the same on your host
// (public/_headers does this for Netlify and Cloudflare Pages).
const securityHeaders = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

function cspMetaTag(policy: string): Plugin {
  return {
    name: "trendify-csp",
    apply: "build", // the dev server's hot reload needs inline scripts, so only on build
    transformIndexHtml: () => [
      {
        tag: "meta",
        attrs: { "http-equiv": "Content-Security-Policy", content: policy },
        injectTo: "head-prepend",
      },
    ],
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const apiUrl = env["VITE_API_URL"];
  const apiOrigin = apiUrl && /^https?:\/\//.test(apiUrl) ? new URL(apiUrl).origin : "";

  return {
    plugins: [
      // Must come before react(): generates src/routeTree.gen.ts from src/routes/
      tanstackRouter({ target: "react", autoCodeSplitting: true }),
      react(),
      tailwindcss(),
      cspMetaTag(contentSecurityPolicy(apiOrigin)),
    ],
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
    server: {
      headers: securityHeaders,
      // Forward API calls and product images to the Flask backend (server/app.py).
      proxy: {
        "/api": {
          target: "http://127.0.0.1:5000",
          rewrite: (p) => p.replace(/^\/api/, ""),
        },
        "/static": "http://127.0.0.1:5000",
      },
    },
    preview: {
      headers: securityHeaders,
      proxy: {
        "/api": {
          target: "http://127.0.0.1:5000",
          rewrite: (p) => p.replace(/^\/api/, ""),
        },
        "/static": "http://127.0.0.1:5000",
      },
    },
  };
});
