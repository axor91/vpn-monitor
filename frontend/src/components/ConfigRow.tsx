"use client";

import { useState } from "react";
import { Copy, Check, RefreshCw } from "lucide-react";
import type { ConfigEntry } from "@/lib/api";
import { api } from "@/lib/api";
import { cn, countryFlag, relativeTime, latencyColor, formatLatency } from "@/lib/utils";

interface Props {
  config: ConfigEntry;
}

export function ConfigRow({ config }: Props) {
  const [c, setC] = useState(config);
  const [copied, setCopied] = useState(false);
  const [checking, setChecking] = useState(false);

  const ok = c.status === "success";

  const copy = () => {
    navigator.clipboard.writeText(c.link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const recheck = async () => {
    if (checking) return;
    setChecking(true);
    try {
      const result = await api.testLink(c.link);
      setC((prev) => ({
        ...prev,
        status: result.status,
        latency: result.latency ?? null,
        geo: result.geo ?? prev.geo,
        error: result.msg,
        checked_at: new Date().toISOString().replace("T", " ").slice(0, 19),
      }));
    } catch {
      // silent
    }
    setChecking(false);
  };

  const dotClass = ok
    ? "bg-success"
    : c.status === "unsupported"
      ? "bg-zinc-600"
      : "bg-danger";

  const fl = c.geo ? countryFlag(c.geo.code) : "";

  return (
    <div className="flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2.5 border-b border-border/30 last:border-b-0 hover:bg-bg-hover transition-colors group">
      {/* Status dot */}
      <div className={cn("w-2 h-2 rounded-full shrink-0", dotClass)} />

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-zinc-200 truncate">{c.name}</div>
        <div className="flex items-center gap-1.5 sm:gap-2 mt-0.5 flex-wrap">
          <span className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 rounded text-[10px] font-bold uppercase tracking-wider">
            {c.protocol}
          </span>
          <span className="text-[11px] text-muted truncate max-w-[100px] sm:max-w-[140px]">{c.address}</span>
          {c.geo && (
            <span className="text-[11px] text-zinc-400 truncate max-w-[120px] sm:max-w-none">
              {fl} {c.geo.country}
            </span>
          )}
          {c.checked_at && (
            <span className="hidden sm:inline text-[10px] text-zinc-600">{relativeTime(c.checked_at)}</span>
          )}
          {!ok && c.error && (
            <span className="text-[10px] text-danger truncate max-w-[100px] sm:max-w-[150px]">{c.error}</span>
          )}
        </div>
      </div>

      {/* Latency */}
      <div className={cn("text-xs font-bold min-w-[50px] text-right shrink-0", latencyColor(c.latency))}>
        {ok ? formatLatency(c.latency) : "—"}
      </div>

      {/* Recheck */}
      <button
        onClick={recheck}
        disabled={checking}
        title="Перепроверить профиль"
        className={cn(
          "shrink-0 flex items-center justify-center w-8 h-8 rounded-md transition-all",
          "sm:opacity-0 sm:group-hover:opacity-100",
          checking
            ? "text-zinc-500 cursor-not-allowed"
            : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800"
        )}
      >
        <RefreshCw size={13} className={cn(checking && "animate-spin")} />
      </button>

      {/* Copy */}
      <button
        onClick={copy}
        className={cn(
          "shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium transition-all min-h-[32px]",
          "sm:opacity-0 sm:group-hover:opacity-100",
          copied
            ? "bg-success text-white"
            : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 border border-border"
        )}
      >
        {copied ? <Check size={12} /> : <Copy size={12} />}
        <span className="hidden sm:inline">{copied ? "OK" : "Копировать"}</span>
      </button>
    </div>
  );
}
