"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronRight, Zap, XCircle, Signal, ShieldCheck } from "lucide-react";
import type { SourceSummary, ConfigEntry } from "@/lib/api";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ConfigRow } from "./ConfigRow";

interface Props {
  source: SourceSummary;
  category: "white" | "black";
  isChecking?: boolean;
}

export function SourceCard({ source, category, isChecking = false }: Props) {
  const [open, setOpen] = useState(false);
  const [configs, setConfigs] = useState<ConfigEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<"all" | "alive" | "dead" | "shutdown">("all");
  // Track the data version we loaded so we can refresh after a re-check.
  const loadedFetchedAt = useRef<string | null>(null);
  const wasChecking = useRef(isChecking);

  const loadConfigs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSource(source.id);
      setConfigs(data.configs || []);
      loadedFetchedAt.current = source.fetched_at;
    } catch {
      // keep previous
    }
    setLoading(false);
  }, [source.id, source.fetched_at]);

  const toggle = () => {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (configs.length === 0 || loadedFetchedAt.current !== source.fetched_at) {
      void loadConfigs();
    }
  };

  // Refresh the open card on new results. fetched_at alone is insufficient: the
  // backend stamps it at the *start* of a re-check while configs are still
  // partial, so also refetch when a check finishes (is_checking true → false).
  useEffect(() => {
    const justFinished = wasChecking.current && !isChecking;
    wasChecking.current = isChecking;
    if (open && (loadedFetchedAt.current !== source.fetched_at || justFinished)) {
      void loadConfigs();
    }
  }, [open, source.fetched_at, isChecking, loadConfigs]);

  const filtered = configs
    .filter((c) => {
      if (filter === "alive") return c.status === "success";
      if (filter === "dead") return c.status !== "success";
      if (filter === "shutdown") return c.status === "success" && c.shutdown_ready;
      return true;
    })
    .sort((a, b) => {
      // shutdown_ready alive first
      if (a.shutdown_ready && !b.shutdown_ready) return -1;
      if (!a.shutdown_ready && b.shutdown_ready) return 1;
      if (a.status === "success" && b.status !== "success") return -1;
      if (a.status !== "success" && b.status === "success") return 1;
      if (a.latency && b.latency) return a.latency - b.latency;
      return 0;
    });

  return (
    <div className="glass glass-hover overflow-hidden">
      {/* Header */}
      <button
        onClick={toggle}
        className="w-full flex items-center gap-3 p-3 sm:p-4 text-left hover:bg-bg-hover transition-colors"
        aria-expanded={open}
      >
        <ChevronRight
          size={14}
          className={cn(
            "text-muted transition-transform duration-200 shrink-0",
            open && "rotate-90"
          )}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold truncate max-w-[180px] sm:max-w-none">{source.label}</span>
            <span
              className={cn(
                "shrink-0 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider",
                category === "white"
                  ? "bg-accent-dim text-accent-light"
                  : "bg-zinc-700/50 text-zinc-400"
              )}
            >
              {category === "white" ? "Для отключений" : "Обычный VPN"}
            </span>
          </div>
          {/* Stats — below label on mobile, inline on desktop */}
          <div className="flex items-center gap-3 sm:gap-4 mt-1.5 sm:mt-1 text-xs text-muted">
            <span className="flex items-center gap-1 text-success">
              <Zap size={12} />
              {source.alive}
            </span>
            {source.shutdown_ready > 0 && (
              <span className="flex items-center gap-1 text-emerald-400">
                <ShieldCheck size={12} />
                {source.shutdown_ready}
              </span>
            )}
            <span className="flex items-center gap-1 text-danger">
              <XCircle size={12} />
              {source.dead}
            </span>
            {source.avg_latency > 0 && (
              <span className="flex items-center gap-1 text-warn">
                <Signal size={12} />
                {source.avg_latency}ms
              </span>
            )}
            <span>{source.total_links} всего</span>
          </div>
        </div>
      </button>

      {/* Body */}
      {open && (
        <div className="border-t border-border animate-fade-in">
          {/* Filter bar */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/50 bg-bg/50">
            {(["all", "alive", "shutdown", "dead"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium transition-colors",
                  filter === f
                    ? "bg-accent text-white"
                    : "text-muted hover:text-zinc-300 hover:bg-zinc-800"
                )}
              >
                {f === "all" ? "Все" : f === "alive" ? "Живые" : f === "shutdown" ? "Для откл." : "Мёртвые"}
              </button>
            ))}
          </div>

          {/* Configs */}
          <div className="max-h-[500px] overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center text-muted text-sm">Загрузка...</div>
            ) : filtered.length === 0 ? (
              <div className="p-8 text-center text-muted text-sm">Нет конфигов</div>
            ) : (
              filtered.map((cfg, i) => <ConfigRow key={i} config={cfg} />)
            )}
          </div>
        </div>
      )}
    </div>
  );
}
