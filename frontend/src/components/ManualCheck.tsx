"use client";

import { useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { TestResult } from "@/lib/api";
import { cn, countryFlag, formatLatency, latencyColor } from "@/lib/utils";
import { toast } from "./Toast";

interface ResultItem {
  link: string;
  name: string;
  result: TestResult | null;
  loading: boolean;
}

export function ManualCheck() {
  const [text, setText] = useState("");
  const [results, setResults] = useState<ResultItem[]>([]);
  const [running, setRunning] = useState(false);

  const run = async () => {
    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.includes("://"));
    if (!lines.length) {
      toast("Вставьте ссылки!", "error");
      return;
    }

    setRunning(true);
    const items: ResultItem[] = lines.map((link) => {
      let name = "Config";
      try {
        if (link.includes("#")) name = decodeURIComponent(link.split("#").pop()!);
      } catch {}
      return { link, name, result: null, loading: true };
    });
    setResults([...items]);

    for (let i = 0; i < items.length; i++) {
      try {
        const result = await api.testLink(items[i].link);
        items[i] = { ...items[i], result, loading: false };
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Ошибка";
        if (msg.includes("429") || msg.includes("Слишком много")) {
          await new Promise((r) => setTimeout(r, 5000));
          i--;
          continue;
        }
        items[i] = { ...items[i], result: { status: "error", msg }, loading: false };
      }
      setResults([...items]);
    }
    setRunning(false);
  };

  const copyLink = (link: string) => {
    navigator.clipboard.writeText(link).then(() => toast("Скопировано!", "success"));
  };

  return (
    <div className="space-y-4">
      <div className="glass p-5 space-y-4">
        <div>
          <h3 className="text-sm font-semibold mb-1">Ручная проверка</h3>
          <p className="text-xs text-muted">
            Вставьте vless://, vmess://, ss://, trojan:// ссылки (по одной на строку)
          </p>
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={"vless://...\nvmess://...\nss://..."}
          className="w-full h-32 bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent resize-none font-mono"
        />
        <button
          onClick={run}
          disabled={running}
          className={cn(
            "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all",
            running
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-accent text-white hover:bg-accent/80"
          )}
        >
          {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {running ? `Проверка...` : "Проверить"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="glass overflow-hidden">
          {results.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-3 border-b border-border/30 last:border-b-0"
            >
              {/* Status */}
              <div
                className={cn(
                  "w-2 h-2 rounded-full shrink-0",
                  item.loading
                    ? "bg-warn animate-pulse"
                    : item.result?.status === "success"
                      ? "bg-success"
                      : "bg-danger"
                )}
              />

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-zinc-200 truncate">{item.name}</div>
                {item.result && (
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    {item.result.geo && (
                      <span className="text-[11px] text-zinc-400">
                        {countryFlag(item.result.geo.code)} {item.result.geo.country} (
                        {item.result.geo.isp})
                      </span>
                    )}
                    {item.result.geo?.ip && (
                      <span className="text-[10px] text-muted">IP: {item.result.geo.ip}</span>
                    )}
                    {item.result.msg && (
                      <span className="text-[10px] text-danger">{item.result.msg}</span>
                    )}
                  </div>
                )}
                {item.loading && (
                  <span className="text-[11px] text-muted">Проверка...</span>
                )}
              </div>

              {/* Latency */}
              <div
                className={cn(
                  "text-xs font-bold min-w-[50px] text-right shrink-0",
                  latencyColor(item.result?.latency ?? null)
                )}
              >
                {item.loading
                  ? "..."
                  : item.result?.status === "success"
                    ? formatLatency(item.result.latency ?? null)
                    : "✕"}
              </div>

              {/* Copy */}
              {!item.loading && (
                <button
                  onClick={() => copyLink(item.link)}
                  className="shrink-0 px-2.5 py-1.5 rounded-md text-[11px] font-medium bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 border border-border transition-all"
                >
                  Копировать
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
