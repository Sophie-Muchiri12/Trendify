import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { PageError, PageLoading } from "@/components/RouteStates";

export const router = createRouter({
  routeTree,
  scrollRestoration: true,
  defaultPreloadStaleTime: 0,
  defaultPendingComponent: PageLoading,
  defaultErrorComponent: PageError,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
