import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, safeRedirect } from "@/lib/api";

describe("safeRedirect", () => {
  it("keeps same-site paths", () => {
    expect(safeRedirect("/account/orders")).toBe("/account/orders");
  });

  it.each([
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "javascript:alert(1)",
    undefined,
  ])("rejects %s", (target) => {
    expect(safeRedirect(target)).toBe("/");
  });
});

describe("api()", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    document.cookie = "csrf_access_token=; max-age=0";
    document.cookie = "csrf_refresh_token=; max-age=0";
  });

  const json = (status: number, body: unknown) =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

  it("sends the CSRF cookie value as a header on state-changing requests", async () => {
    document.cookie = "csrf_access_token=abc123";
    const fetchMock = vi.fn().mockResolvedValue(json(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await api("/orders", { method: "POST", body: { a: 1 } });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>)["X-CSRF-TOKEN"]).toBe("abc123");
    expect(init.credentials).toBe("include");
  });

  it("does not add the CSRF header to GET requests", async () => {
    document.cookie = "csrf_access_token=abc123";
    const fetchMock = vi.fn().mockResolvedValue(json(200, {}));
    vi.stubGlobal("fetch", fetchMock);

    await api("/products");
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>)["X-CSRF-TOKEN"]).toBeUndefined();
  });

  it("refreshes the session once on 401 and retries", async () => {
    document.cookie = "csrf_refresh_token=r1";
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json(401, { error: "expired", code: "token_expired" }))
      .mockResolvedValueOnce(json(200, {})) // /auth/refresh
      .mockResolvedValueOnce(json(200, { items: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api("/orders")).resolves.toEqual({ items: [] });
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual([
      "/api/orders",
      "/api/auth/refresh",
      "/api/orders",
    ]);
  });

  it("turns error responses into ApiError with field messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json(400, { error: "Bad", fields: { email: ["Invalid"] } })),
    );
    const err = await api("/auth/register", { method: "POST", body: {} }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).field("email")).toBe("Invalid");
  });
});
