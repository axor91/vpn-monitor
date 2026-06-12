import { describe, expect, it } from "vitest";
import { countryFlag, formatLatency, latencyColor, relativeTime } from "@/lib/utils";

describe("relativeTime", () => {
  it("returns dash for null", () => {
    expect(relativeTime(null)).toBe("—");
  });

  it("formats seconds/minutes/hours ago (UTC input from backend)", () => {
    // Backend emits UTC (ISO with Z); relativeTime must compare in UTC.
    const ago = (s: number) => new Date(Date.now() - s * 1000).toISOString();
    expect(relativeTime(ago(10))).toMatch(/с назад$/);
    expect(relativeTime(ago(120))).toBe("2м назад");
    expect(relativeTime(ago(7200))).toBe("2ч назад");
  });

  it("treats a zone-less timestamp as UTC, not browser-local", () => {
    // The TZ bug: "YYYY-MM-DD HH:MM:SS" must parse identically to the same
    // instant with an explicit Z, regardless of the viewer's offset.
    const d = new Date(Date.now() - 90 * 1000);
    const iso = d.toISOString(); // "...T..:..:..Z"
    const zoneless = iso.replace("T", " ").slice(0, 19); // "YYYY-MM-DD HH:MM:SS"
    expect(relativeTime(zoneless)).toBe(relativeTime(iso));
    expect(relativeTime(zoneless)).toBe("1м назад");
  });

  it("returns the raw string for dates older than a day", () => {
    const old = "2020-01-01 00:00:00";
    expect(relativeTime(old)).toBe(old);
  });
});

describe("countryFlag", () => {
  it("returns empty for missing or UN code", () => {
    expect(countryFlag(undefined)).toBe("");
    expect(countryFlag("UN")).toBe("");
  });

  it("maps a country code to regional-indicator emoji", () => {
    // RU → 🇷🇺 (U+1F1F7 U+1F1FA)
    expect(countryFlag("RU")).toBe("\u{1F1F7}\u{1F1FA}");
    expect(countryFlag("ru")).toBe("\u{1F1F7}\u{1F1FA}"); // case-insensitive
  });
});

describe("formatLatency", () => {
  it("returns dash for null", () => {
    expect(formatLatency(null)).toBe("—");
  });

  it("uses ms under 1000 and seconds above", () => {
    expect(formatLatency(50)).toBe("50ms");
    expect(formatLatency(450)).toBe("450ms");
    expect(formatLatency(1500)).toBe("1.5s");
  });
});

describe("latencyColor", () => {
  it("buckets by threshold", () => {
    expect(latencyColor(null)).toBe("text-muted");
    expect(latencyColor(100)).toBe("text-success");
    expect(latencyColor(500)).toBe("text-warn");
    expect(latencyColor(1200)).toBe("text-danger");
  });
});
