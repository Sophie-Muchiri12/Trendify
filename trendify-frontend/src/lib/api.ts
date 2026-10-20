/**
 * Small fetch wrapper for the Flask API.
 *
 * - Sessions live in HttpOnly cookies set by the server, so JavaScript never sees the
 *   tokens. Every request sends cookies (`credentials: "include"`).
 * - State-changing requests echo the readable `csrf_*` cookie in an X-CSRF-TOKEN header
 *   (double-submit CSRF protection).
 * - A 401 triggers one silent refresh using the refresh cookie, then the request is retried.
 */

// In dev, Vite proxies /api and /static to the Flask server (see vite.config.ts).
export const API_URL: string = import.meta.env["VITE_API_URL"] ?? "/api";

export class ApiError extends Error {
  status: number;
  code: string | undefined;
  fields: Record<string, string[] | Record<string, unknown>> | undefined;

  constructor(status: number, message: string, code?: string, fields?: ApiError["fields"]) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }

  /** First message for a form field, if the server reported one. */
  field(name: string): string | undefined {
    const value = this.fields?.[name];
    if (Array.isArray(value)) return value.join(" ");
    if (value && typeof value === "object") return "Please check this field.";
    return undefined;
  }
}

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export const hasRefreshCookie = () => Boolean(readCookie("csrf_refresh_token"));

let refreshing: Promise<boolean> | null = null;

/** Ask the server for a new access cookie. Concurrent callers share one request. */
export function refreshSession(): Promise<boolean> {
  if (!hasRefreshCookie()) return Promise.resolve(false);
  refreshing ??= fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-TOKEN": readCookie("csrf_refresh_token") ?? "" },
  })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

type Options = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  form?: FormData;
  headers?: Record<string, string>;
};

const NO_REFRESH = ["/auth/login", "/auth/refresh", "/auth/logout", "/auth/register"];

export async function api<T = unknown>(path: string, opts: Options = {}, retry = true): Promise<T> {
  const method = opts.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json", ...opts.headers };
  let body: BodyInit | null = null;
  if (opts.form) {
    body = opts.form;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  if (method !== "GET") {
    const csrf = readCookie("csrf_access_token");
    if (csrf) headers["X-CSRF-TOKEN"] = csrf;
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { method, headers, body, credentials: "include" });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }

  if (res.status === 401 && retry && !NO_REFRESH.some((p) => path.startsWith(p))) {
    if (await refreshSession()) return api<T>(path, opts, false);
  }

  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new ApiError(
      res.status,
      typeof data["error"] === "string" ? data["error"] : `Request failed (HTTP ${res.status})`,
      typeof data["code"] === "string" ? data["code"] : undefined,
      data["fields"] as ApiError["fields"],
    );
  }
  return data as T;
}

/** A random key so a retried checkout can't create a second order. */
export function idempotencyKey(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

/** Only allow redirects back into this site (prevents open-redirect phishing). */
export function safeRedirect(target: string | undefined): string {
  return target && target.startsWith("/") && !target.startsWith("//") && !target.startsWith("/\\")
    ? target
    : "/";
}
