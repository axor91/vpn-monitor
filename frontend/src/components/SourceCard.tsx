"use client";

import { useState } from "react";
import { ChevronRight, Zap, XCircle, Signal, RefreshCw } from "lucide-react";
import type { SourceSummary, ConfigEntry } from "@/lib/api";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "./Toast";
import { ConfigRow } from "./ConfigRow";

interface Props {
  source: SourceSummary;
  category: "white" | "black";
}

export function SourceCard({ source, category }: Props) {
  const [open, setOpen] = useState(false);
  const [configs, setConfigs] = useState<ConfigEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<"all" | "alive" | "dead">("all");
  const [checking, setChecking] = useState(false);

  const toggle = async () => {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (configs.length === 0) {
      setLoading(true);
      try {
        const data = await api.getSource(source.id);
        setConfigs(data.configs || []);
      } catch {
        // keep empty
      }
      setLoading(false);
    }
  };

  const refreshConfigs = async () => {
    try {
      const data = await api.getSource(source.id);
      setConfigs(data.configs || []);
    } catch {
      // silent
    }
  };

  const handleCheck = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (checking) return;
    setChecking(true);
    try {
      await api.checkSource(source.id);
      toast(`Проверка «${source.label}» запущена`, "success");
      // Poll for updates while source is being checked
      const poll = setInterval(async () => {
        try {
          const data = await api.getSource(source.id);
          if (!data._checking) {
            clearInterval(poll);
            setChecking(false);
            setConfigs(data.configs || []);
          } else {
            setConfigs(data.configs || []);
          }
        } catch {
          clearInterval(poll);
          setChecking(false);
        }
      }, 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка";
      toast(msg, "error");
      setChecking(false);
    }
  };

  const filtered = configs
    .filter((c) => {
      if (filter === "alive") return c.status === "success";
      if (filter === "dead") return c.status !== "success";
      return true;
    })
    .sort((a, b) => {
      if (a.status === "success" && b.status !== "success") return -1;
      if (a.status !== "success" && b.status === "success") return 1;
      if (a.latency && b.latency) return a.latency - b.latency;
      return 0;
    });

  return (
    <div className="glass glass-hover overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 p-3 sm:p-4 hover:bg-bg-hover transition-colors">
        <div
          role="button"
          tabIndex={0}
          onClick={toggle}
          onKeyDown={(e) => e.key === "Enter" && toggle()}
          aria-expanded={open}
          className="flex items-center gap-3 flex-1 min-w-0 cursor-pointer"
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
        </div>

        {/* Per-source refresh */}
        <button
          onClick={handleCheck}
          disabled={checking}
          title="Перепроверить источник"
          className={cn(
            "shrink-0 flex items-center gap-1.5 px-2 sm:px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all",
            checking
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 border border-border"
          )}
        >
          <RefreshCw size={13} className={cn(checking && "animate-spin")} />
          <span className="hidden sm:inline">{checking ? "Проверка..." : "Обновить"}</span>
        </button>
      </div>

      {/* Body */}
      {open && (
        <div className="border-t border-border animate-fade-in">
          {/* Filter bar */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/50 bg-bg/50">
            {(["all", "alive", "dead"] as const).map((f) => (
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
                {f === "all" ? "Все" : f === "alive" ? "Живые" : "Мёртвые"}
              </button>
            ))}
            <button
              onClick={refreshConfigs}
              className="ml-auto text-xs text-muted hover:text-zinc-300 transition-colors"
            >
              Обновить
            </button>
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
