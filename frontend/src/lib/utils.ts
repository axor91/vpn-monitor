import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function relativeTime(dt: string | null): string {
  if (!dt) return "—";
  try {
    const d = new Date(dt.replace(" ", "T"));
    const now = new Date();
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diff < 60) return `${diff}с назад`;
    if (diff < 3600) return `${Math.floor(diff / 60)}м назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}ч назад`;
    return dt;
  } catch {
    return dt;
  }
}

export function countryFlag(code: string | undefined): string {
  if (!code || code === "UN") return "";
  return code
    .toUpperCase()
    .replace(/./g, (c) => String.fromCodePoint(c.charCodeAt(0) + 127397));
}

export function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 100) return `${ms}ms`;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function latencyColor(ms: number | null): string {
  if (ms === null) return "text-muted";
  if (ms < 300) return "text-success";
  if (ms < 800) return "text-warn";
  return "text-danger";
}
