"use client";

import { Activity, Clock, Wifi, Square } from "lucide-react";
import type { SummaryData } from "@/lib/api";
import { relativeTime } from "@/lib/utils";

interface Props {
  data: SummaryData | null;
  onStop: () => void;
}

export function StatusBar({ data, onStop }: Props) {
  if (!data) {
    return (
      <div className="glass p-4 animate-pulse">
        <div className="h-5 bg-zinc-800 rounded w-48" />
      </div>
    );
  }

  const isChecking = data.is_checking;
  const progress = data.check_progress;
  const progressKeys = Object.keys(progress);

  let totalCur = 0;
  let totalMax = 0;
  const parts: string[] = [];
  for (const k of progressKeys) {
    const p = progress[k];
    totalCur += p.current;
    totalMax += p.total;
    parts.push(`${p.source} ${p.current}/${p.total}`);
  }
  const pct = totalMax > 0 ? Math.round((totalCur / totalMax) * 100) : 0;

  const totalAlive =
    [...(data.white || []), ...(data.black || [])].reduce((s, src) => s + src.alive, 0);

  return (
    <div className="glass p-4 sm:p-5">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Status indicator */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                isChecking ? "bg-warn animate-pulse-slow" : "bg-success"
              }`}
            />
            {isChecking && (
              <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-warn/40 animate-ping" />
            )}
          </div>
          <span className="text-sm font-semibold">
            {isChecking ? "Проверка идёт..." : "Готово"}
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-5 text-xs text-muted">
          <div className="flex items-center gap-1.5">
            <Clock size={13} />
            <span>{relativeTime(data.last_update) || "Не проверялось"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Wifi size={13} />
            <span className="text-success font-semibold">{totalAlive}</span>
            <span>живых</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Activity size={13} />
            <span>{data.white.length + data.black.length} источников</span>
          </div>
        </div>

        {/* Stop button */}
        {isChecking && (
          <button
            onClick={onStop}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-danger border border-danger/30 rounded-lg hover:bg-danger/10 transition-colors"
          >
            <Square size={12} />
            Стоп
          </button>
        )}
      </div>

      {/* Progress bar */}
      {isChecking && progressKeys.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted">
            <span className="truncate max-w-[80%]">{parts.join("  ·  ")}</span>
            <span className="font-mono text-zinc-400">{pct}%</span>
          </div>
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent to-accent-light rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
