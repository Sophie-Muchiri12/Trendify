import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Page } from "@/lib/products";

/** Load a paginated admin list and reload it on demand. */
export function useAdminList<T>(path: string) {
  const [data, setData] = useState<Page<T> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const reload = useCallback(() => {
    setError(null);
    api<Page<T>>(path).then(setData).catch(setError);
  }, [path]);
  useEffect(reload, [reload]);
  return { data, error, reload };
}

export function query(params: Record<string, string | number | undefined>) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params))
    if (v !== undefined && v !== "") qs.set(k, String(v));
  const s = qs.toString();
  return s ? `?${s}` : "";
}
