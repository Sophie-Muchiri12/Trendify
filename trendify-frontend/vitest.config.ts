import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

// Reuses the Vite config so the router plugin generates routeTree.gen.ts for tests too.
export default defineConfig((env) =>
  mergeConfig(viteConfig(env), {
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.{test,spec}.{ts,tsx}"],
    },
  }),
);
