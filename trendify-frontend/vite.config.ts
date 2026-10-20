import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";

export default defineConfig({
  plugins: [
    // Must come before react(): generates src/routeTree.gen.ts from src/routes/
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    // Forward API calls and product images to the Flask backend (server/app.py).
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/static": "http://127.0.0.1:5000",
    },
  },
});
