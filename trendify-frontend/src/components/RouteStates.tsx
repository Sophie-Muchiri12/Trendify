import { useRouter, type ErrorComponentProps } from "@tanstack/react-router";

export function PageLoading() {
  return <p className="py-32 text-center text-muted-foreground">Loading…</p>;
}

export function PageError({ error, reset }: ErrorComponentProps) {
  const router = useRouter();
  return (
    <div className="py-32 text-center">
      <h1 className="text-4xl">Something went wrong</h1>
      <p className="mt-3 text-muted-foreground">
        {error instanceof Error ? error.message : "Please try again."}
      </p>
      <button
        onClick={() => {
          reset();
          void router.invalidate();
        }}
        className="mt-6 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground"
      >
        Try again
      </button>
    </div>
  );
}
