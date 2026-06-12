import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("getSummary hits the namespaced path and returns parsed JSON", async () => {
    const fetchMock = mockFetch(200, { black: [], white: [] });
    vi.stubGlobal("fetch", fetchMock);

    const data = await api.getSummary();

    expect(fetchMock).toHaveBeenCalledWith("/vpn-monitor/api/summary", undefined);
    expect(data).toEqual({ black: [], white: [] });
  });

  it("testLink POSTs JSON body to the test_link endpoint", async () => {
    const fetchMock = mockFetch(200, { status: "success", latency: 42 });
    vi.stubGlobal("fetch", fetchMock);

    await api.testLink("vless://x@h:443");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/vpn-monitor/api/test_link");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ link: "vless://x@h:443" });
  });

  it("throws the server error message on non-2xx", async () => {
    vi.stubGlobal("fetch", mockFetch(429, { error: "Слишком много запросов" }));
    await expect(api.testLink("vless://x")).rejects.toThrow("Слишком много запросов");
  });

  it("falls back to HTTP status when no error field", async () => {
    vi.stubGlobal("fetch", mockFetch(500, {}));
    await expect(api.getSummary()).rejects.toThrow("HTTP 500");
  });
});
